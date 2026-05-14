"""Task Review Skill Adapter"""
import os
import sys
sys.path.insert(0, os.path.expanduser('~/Repos/agent-factory/src'))

from core.task_manager import TaskManager
from core.model_router import ModelRouter
from core.state_machine import StateMachine


class TaskReviewSkill:
    """Review completed work and provide feedback"""
    
    def __init__(self, config=None):
        self.task_manager = TaskManager()
        self.model_router = ModelRouter()
        self.state_machine = StateMachine()
    
    async def execute(self, task_id: str, context: dict = None) -> dict:
        """
        Review a completed task.
        
        OpenClaw calls this when user says:
        "Review task #0001" or "Check if the authentication is done correctly"
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}
        
        # Check if task can be reviewed
        if not self.state_machine.can_transition(task, "submit-for-review"):
            return {
                "error": f"Task {task_id} is not ready for review",
                "current_state": task.state,
                "available_actions": self.state_machine.get_available_actions(task)
            }
        
        # Select review model (prefer premium for reviews)
        model_id = self.model_router.select_model(
            task_type="review",
            complexity=task.complexity,
            required_capabilities=["reasoning"]
        )
        
        if not model_id:
            return {"error": "No suitable model available for review"}
        
        # Transition state
        self.state_machine.transition(task, "submit-for-review")
        self.task_manager.update_task(task)
        
        # Generate review checklist
        review_criteria = self._generate_review_checklist(task)
        
        return {
            "task_id": task.id,
            "reviewer_model": model_id,
            "state": task.state,
            "checklist": review_criteria,
            "message": f"Task {task_id} submitted for review using {model_id}"
        }
    
    def _generate_review_checklist(self, task) -> list:
        """Generate review checklist based on task type"""
        checklist = []
        
        # Standard items
        checklist.extend([
            f"✓ Acceptance criteria met: {len(task.acceptance_criteria)} items",
            "✓ Code follows style guidelines",
            "✓ Tests pass",
            "✓ No security vulnerabilities"
        ])
        
        # Complexity-based items
        if task.complexity >= 4:
            checklist.extend([
                "✓ Architecture reviewed",
                "✓ Performance impact assessed",
                "✓ Documentation updated"
            ])
        
        return checklist
    
    async def approve(self, task_id: str) -> dict:
        """Approve a reviewed task"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}
        
        if self.state_machine.transition(task, "approve", approved=True):
            self.task_manager.update_task(task)
            return {
                "task_id": task.id,
                "state": task.state,
                "message": f"Task {task_id} approved"
            }
        
        return {"error": "Cannot approve task", "current_state": task.state}
    
    async def request_changes(self, task_id: str, feedback: str) -> dict:
        """Request changes on a reviewed task"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}
        
        if self.state_machine.transition(task, "request-changes"):
            # Add feedback to task
            task.description += f"\n\n## Review Feedback\n{feedback}"
            self.task_manager.update_task(task)
            
            return {
                "task_id": task.id,
                "state": task.state,
                "message": f"Changes requested for task {task_id}"
            }
        
        return {"error": "Cannot request changes", "current_state": task.state}


# OpenClaw entry point
def main(task_id: str, action: str = "review", feedback: str = "", **kwargs) -> dict:
    """OpenClaw calls this function"""
    import asyncio
    skill = TaskReviewSkill()
    
    if action == "review":
        return asyncio.run(skill.execute(task_id, kwargs.get("context")))
    elif action == "approve":
        return asyncio.run(skill.approve(task_id))
    elif action == "request-changes":
        return asyncio.run(skill.request_changes(task_id, feedback))
    else:
        return {"error": f"Unknown action: {action}"}


if __name__ == "__main__":
    import asyncio
    # Test
    result = asyncio.run(TaskReviewSkill().execute("0001"))
    print(result)
