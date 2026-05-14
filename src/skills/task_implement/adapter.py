"""Task Implement Skill Adapter"""
import os
import sys
sys.path.insert(0, os.path.expanduser('~/Repos/agent-factory/src'))

from core.task_manager import TaskManager
from core.model_router import ModelRouter
from core.state_machine import StateMachine


class TaskImplementSkill:
    """Execute implementation tasks using LLMs"""
    
    def __init__(self, config=None):
        self.task_manager = TaskManager()
        self.model_router = ModelRouter()
        self.state_machine = StateMachine()
    
    async def execute(self, task_id: str, context: dict = None) -> dict:
        """
        Implement a task from spec.
        
        OpenClaw calls this when user says:
        "Implement task #0001" or "Start work on authentication"
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}
        
        # Check if task can transition to in-progress
        if not self.state_machine.can_transition(task, "start-implementation"):
            return {
                "error": f"Task {task_id} cannot be started",
                "current_state": task.state,
                "available_actions": self.state_machine.get_available_actions(task)
            }
        
        # Select model based on task complexity
        model_id = self.model_router.select_model(
            task_type="implementation",
            complexity=task.complexity,
            priority=task.priority
        )
        
        if not model_id:
            return {"error": "No suitable model available"}
        
        # Update task
        task.assigned_model = model_id
        task.estimated_cost = self._estimate_cost(task, model_id)
        
        # Transition state
        self.state_machine.transition(task, "start-implementation")
        self.task_manager.update_task(task)
        
        return {
            "task_id": task.id,
            "model": model_id,
            "estimated_cost": task.estimated_cost,
            "state": task.state,
            "message": f"Task {task_id} assigned to {model_id} for implementation"
        }
    
    def _estimate_cost(self, task, model_id: str) -> float:
        """Estimate implementation cost"""
        config = self.model_router.get_model_config(model_id)
        if not config:
            return 0.0
        
        # Rough estimate: 2k input tokens, 4k output tokens for medium task
        complexity_multiplier = task.complexity / 3.0
        input_tokens = int(2000 * complexity_multiplier)
        output_tokens = int(4000 * complexity_multiplier)
        
        return self.model_router.estimate_cost(model_id, input_tokens, output_tokens)


# OpenClaw entry point
def main(task_id: str, **kwargs) -> dict:
    """OpenClaw calls this function"""
    import asyncio
    skill = TaskImplementSkill()
    return asyncio.run(skill.execute(task_id, kwargs.get("context")))


if __name__ == "__main__":
    import asyncio
    # Test
    result = asyncio.run(TaskImplementSkill().execute("0001"))
    print(result)
