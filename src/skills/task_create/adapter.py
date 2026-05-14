"""Task Create Skill Adapter"""
import os
import sys
sys.path.insert(0, os.path.expanduser('~/Repos/agent-factory/src'))

from core.task_manager import TaskManager
from core.model_router import ModelRouter


class TaskCreateSkill:
    """OpenClaw skill for creating tasks"""
    
    def __init__(self, config=None):
        self.task_manager = TaskManager()
        self.model_router = ModelRouter()
    
    async def execute(self, request: str, context: dict = None) -> dict:
        """Create task from natural language"""
        # TODO: Implement LLM-based task generation
        task = self.task_manager.create_task(
            title=request[:50],
            description=request,
            acceptance_criteria=["TBD"],
            tags=["auto-created"]
        )
        
        return {
            "task_id": task.id,
            "title": task.title,
            "dashboard_url": f"http://localhost:8080/tasks/{task.id}"
        }


# OpenClaw entry point
def main(request: str, **kwargs) -> dict:
    """OpenClaw calls this function"""
    import asyncio
    skill = TaskCreateSkill()
    return asyncio.run(skill.execute(request, kwargs.get("context")))


if __name__ == "__main__":
    import asyncio
    result = asyncio.run(TaskCreateSkill().execute("Create a task to implement user authentication"))
    print(result)
