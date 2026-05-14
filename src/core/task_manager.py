"""Task Manager - Create, track, and manage AI tasks"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class Task:
    """Represents a single AI task"""
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    state: str = "backlog"
    complexity: int = 3
    priority: str = "normal"
    created_at: str = ""
    updated_at: str = ""
    assigned_model: str = ""
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    assignee: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_markdown(self) -> str:
        """Convert task to markdown format"""
        criteria = "\n".join([f"- [ ] {c}" for c in self.acceptance_criteria])
        tags = " ".join([f"#{t}" for t in self.tags]) if self.tags else ""
        
        return f"""---
id: {self.id}
title: {self.title}
state: {self.state}
complexity: {self.complexity}
priority: {self.priority}
created_at: {self.created_at}
updated_at: {self.updated_at}
assigned_model: {self.assigned_model}
estimated_cost: {self.estimated_cost}
actual_cost: {self.actual_cost}
assignee: {self.assignee}
tags: {self.tags}
---

# {self.title}

## Description
{self.description}

## Acceptance Criteria
{criteria}

## Notes
<!-- Add implementation notes here -->

## Cost Tracking
- Estimated: ${self.estimated_cost}
- Actual: ${self.actual_cost}
"""


class TaskManager:
    """Manages task lifecycle and storage"""
    
    def __init__(self, data_path: str = "~/Repos/agent-factory-data"):
        self.data_path = Path(data_path).expanduser()
        self.tasks_path = self.data_path / "tasks"
        self.state_path = self.data_path / "state"
        
        # Create directories
        self.tasks_path.mkdir(parents=True, exist_ok=True)
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        self._counter = self._load_counter()
    
    def _load_counter(self) -> int:
        """Load task ID counter"""
        counter_file = self.state_path / "task_counter.txt"
        if counter_file.exists():
            return int(counter_file.read_text().strip())
        return 0
    
    def _save_counter(self):
        """Save task ID counter"""
        counter_file = self.state_path / "task_counter.txt"
        counter_file.write_text(str(self._counter))
    
    def _generate_id(self) -> str:
        """Generate next task ID"""
        self._counter += 1
        self._save_counter()
        return f"{self._counter:04d}"
    
    def create_task(
        self,
        title: str,
        description: str,
        acceptance_criteria: List[str],
        complexity: int = 3,
        priority: str = "normal",
        tags: List[str] = None
    ) -> Task:
        """Create a new task"""
        task = Task(
            id=self._generate_id(),
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            complexity=complexity,
            priority=priority,
            tags=tags or []
        )
        
        # Save to file
        self._save_task(task)
        return task
    
    def _save_task(self, task: Task):
        """Save task to markdown file"""
        task_file = self.tasks_path / f"{task.id}-{self._slugify(task.title)}.md"
        task_file.write_text(task.to_markdown())
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug"""
        return re.sub(r'[^\w\s-]', '', text).strip().lower().replace(' ', '-')[:50]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Load task by ID"""
        # Find file with matching ID
        for task_file in self.tasks_path.glob(f"{task_id}-*.md"):
            return self._parse_task_file(task_file)
        return None
    
    def _parse_task_file(self, task_file: Path) -> Task:
        """Parse markdown task file"""
        content = task_file.read_text()
        
        # Extract YAML frontmatter
        match = re.match(r'^---\n(.*?)\n---\n+(.*)$', content, re.DOTALL)
        if not match:
            raise ValueError(f"Invalid task file format: {task_file}")
        
        frontmatter = match.group(1)
        body = match.group(2)
        
        # Parse frontmatter
        metadata = {}
        for line in frontmatter.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip()
        
        # Parse acceptance criteria from body
        criteria = []
        criteria_match = re.search(r'## Acceptance Criteria\n+((?:- \[.?\] .+\n)+)', body)
        if criteria_match:
            for line in criteria_match.group(1).strip().split('\n'):
                if line.startswith('- [ ] '):
                    criteria.append(line[6:])
        
        return Task(
            id=metadata.get('id', ''),
            title=metadata.get('title', ''),
            description=self._extract_section(body, 'Description'),
            acceptance_criteria=criteria,
            state=metadata.get('state', 'backlog'),
            complexity=int(metadata.get('complexity', 3)),
            priority=metadata.get('priority', 'normal'),
            created_at=metadata.get('created_at', ''),
            updated_at=metadata.get('updated_at', ''),
            assigned_model=metadata.get('assigned_model', ''),
            estimated_cost=float(metadata.get('estimated_cost', 0)),
            actual_cost=float(metadata.get('actual_cost', 0)),
            assignee=metadata.get('assignee', ''),
            tags=eval(metadata.get('tags', '[]'))
        )
    
    def _extract_section(self, body: str, section: str) -> str:
        """Extract section content from markdown body"""
        pattern = f'## {section}\n+(.*?)(?=\n## |$)'
        match = re.search(pattern, body, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    def update_task(self, task: Task) -> Task:
        """Update existing task"""
        task.updated_at = datetime.now().isoformat()
        self._save_task(task)
        return task
    
    def list_tasks(self, state: Optional[str] = None) -> List[Task]:
        """List all tasks, optionally filtered by state"""
        tasks = []
        for task_file in sorted(self.tasks_path.glob("*.md")):
            try:
                task = self._parse_task_file(task_file)
                if state is None or task.state == state:
                    tasks.append(task)
            except Exception:
                continue
        return tasks
    
    def get_stats(self) -> Dict:
        """Get task statistics"""
        tasks = self.list_tasks()
        states = {}
        total_cost = 0.0
        
        for task in tasks:
            states[task.state] = states.get(task.state, 0) + 1
            total_cost += task.actual_cost
        
        return {
            "total": len(tasks),
            "by_state": states,
            "total_cost": round(total_cost, 2)
        }
