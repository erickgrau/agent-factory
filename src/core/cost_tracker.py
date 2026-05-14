"""Cost Tracker - Track and limit spending across models"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CostEntry:
    """Single cost entry"""
    timestamp: str
    model_id: str
    task_id: str
    input_tokens: int
    output_tokens: int
    cost: float
    action: str


class CostTracker:
    """Track costs and enforce budgets"""
    
    def __init__(self, data_path: str = "~/Repos/agent-factory-data"):
        self.data_path = Path(data_path).expanduser()
        self.costs_path = self.data_path / "costs"
        self.costs_path.mkdir(parents=True, exist_ok=True)
        
        self.daily_budget: float = 10.00
        self.per_task_budget: float = 1.00
        self.alert_threshold: float = 0.80
        
        self._load_config()
    
    def _load_config(self):
        """Load budget configuration"""
        config_file = self.data_path / "config" / "budget.yaml"
        if config_file.exists():
            # Parse YAML config
            import yaml
            with open(config_file) as f:
                config = yaml.safe_load(f)
                self.daily_budget = config.get("daily", 10.00)
                self.per_task_budget = config.get("per_task", 1.00)
                self.alert_threshold = config.get("alert_at", 0.80)
    
    def record_cost(
        self,
        model_id: str,
        task_id: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        action: str = "generation"
    ):
        """Record a cost entry"""
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            model_id=model_id,
            task_id=task_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            action=action
        )
        
        # Append to daily log
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.costs_path / f"{today}.jsonl"
        
        with open(log_file, "a") as f:
            f.write(json.dumps({
                "timestamp": entry.timestamp,
                "model_id": entry.model_id,
                "task_id": entry.task_id,
                "input_tokens": entry.input_tokens,
                "output_tokens": entry.output_tokens,
                "cost": entry.cost,
                "action": entry.action
            }) + "\n")
    
    def get_daily_cost(self, date: Optional[str] = None) -> float:
        """Get total cost for a day"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = self.costs_path / f"{date}.jsonl"
        if not log_file.exists():
            return 0.0
        
        total = 0.0
        with open(log_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    total += entry.get("cost", 0)
                except json.JSONDecodeError:
                    continue
        
        return total
    
    def get_task_cost(self, task_id: str) -> float:
        """Get total cost for a task"""
        total = 0.0
        
        # Check last 7 days
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = self.costs_path / f"{date}.jsonl"
            
            if not log_file.exists():
                continue
            
            with open(log_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("task_id") == task_id:
                            total += entry.get("cost", 0)
                    except json.JSONDecodeError:
                        continue
        
        return total
    
    def check_budget(self, task_id: str) -> Dict:
        """Check budget status"""
        daily_cost = self.get_daily_cost()
        task_cost = self.get_task_cost(task_id)
        
        daily_remaining = self.daily_budget - daily_cost
        task_remaining = self.per_task_budget - task_cost
        
        daily_percent = daily_cost / self.daily_budget if self.daily_budget > 0 else 0
        task_percent = task_cost / self.per_task_budget if self.per_task_budget > 0 else 0
        
        return {
            "daily_cost": round(daily_cost, 2),
            "daily_budget": self.daily_budget,
            "daily_remaining": round(daily_remaining, 2),
            "daily_percent": round(daily_percent * 100, 1),
            "task_cost": round(task_cost, 2),
            "task_budget": self.per_task_budget,
            "task_remaining": round(task_remaining, 2),
            "task_percent": round(task_percent * 100, 1),
            "alert": daily_percent >= self.alert_threshold or task_percent >= self.alert_threshold,
            "can_proceed": daily_remaining > 0 and task_remaining > 0
        }
    
    def get_stats(self, days: int = 7) -> Dict:
        """Get cost statistics"""
        stats = {
            "total": 0.0,
            "by_day": {},
            "by_model": {},
            "by_task": {}
        }
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = self.costs_path / f"{date}.jsonl"
            
            if not log_file.exists():
                continue
            
            daily_total = 0.0
            
            with open(log_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        cost = entry.get("cost", 0)
                        daily_total += cost
                        stats["total"] += cost
                        
                        model_id = entry.get("model_id", "unknown")
                        stats["by_model"][model_id] = stats["by_model"].get(model_id, 0) + cost
                        
                        task_id = entry.get("task_id", "unknown")
                        if task_id not in stats["by_task"]:
                            stats["by_task"][task_id] = 0
                        stats["by_task"][task_id] += cost
                    except json.JSONDecodeError:
                        continue
            
            stats["by_day"][date] = round(daily_total, 2)
        
        stats["total"] = round(stats["total"], 2)
        return stats
