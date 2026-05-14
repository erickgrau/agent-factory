"""State Machine - Manage task lifecycle states"""
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class TaskState(Enum):
    """Task states"""
    BACKLOG = "backlog"
    SPEC_DEFINED = "spec-defined"
    PLAN_APPROVED = "plan-approved"
    IN_PROGRESS = "in-progress"
    NEEDS_REVIEW = "needs-review"
    APPROVED = "approved"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass
class Transition:
    """State transition"""
    from_state: TaskState
    to_state: TaskState
    action: str
    requires_approval: bool = False
    auto_execute: Optional[Callable] = None


class StateMachine:
    """Manages task state transitions"""
    
    def __init__(self):
        self.transitions: Dict[str, List[Transition]] = self._define_transitions()
        self.callbacks: Dict[str, List[Callable]] = {}
    
    def _define_transitions(self) -> Dict[str, List[Transition]]:
        """Define valid state transitions"""
        return {
            TaskState.BACKLOG.value: [
                Transition(TaskState.BACKLOG, TaskState.SPEC_DEFINED, "define-spec"),
            ],
            TaskState.SPEC_DEFINED.value: [
                Transition(TaskState.SPEC_DEFINED, TaskState.PLAN_APPROVED, "approve-plan", requires_approval=True),
                Transition(TaskState.SPEC_DEFINED, TaskState.BACKLOG, "reject-spec"),
            ],
            TaskState.PLAN_APPROVED.value: [
                Transition(TaskState.PLAN_APPROVED, TaskState.IN_PROGRESS, "start-implementation"),
                Transition(TaskState.PLAN_APPROVED, TaskState.BLOCKED, "block"),
            ],
            TaskState.IN_PROGRESS.value: [
                Transition(TaskState.IN_PROGRESS, TaskState.NEEDS_REVIEW, "submit-for-review"),
                Transition(TaskState.IN_PROGRESS, TaskState.BLOCKED, "block"),
            ],
            TaskState.NEEDS_REVIEW.value: [
                Transition(TaskState.NEEDS_REVIEW, TaskState.APPROVED, "approve", requires_approval=True),
                Transition(TaskState.NEEDS_REVIEW, TaskState.IN_PROGRESS, "request-changes"),
            ],
            TaskState.APPROVED.value: [
                Transition(TaskState.APPROVED, TaskState.DONE, "mark-done"),
            ],
            TaskState.BLOCKED.value: [
                Transition(TaskState.BLOCKED, TaskState.IN_PROGRESS, "unblock"),
                Transition(TaskState.BLOCKED, TaskState.BACKLOG, "cancel"),
            ],
            TaskState.DONE.value: [
                Transition(TaskState.DONE, TaskState.BACKLOG, "reopen"),
            ],
        }
    
    def can_transition(self, task, action: str) -> bool:
        """Check if transition is valid"""
        current_state = task.state
        if current_state not in self.transitions:
            return False
        
        for transition in self.transitions[current_state]:
            if transition.action == action:
                return True
        return False
    
    def transition(self, task, action: str, approved: bool = False) -> bool:
        """Execute state transition"""
        if not self.can_transition(task, action):
            return False
        
        current_state = task.state
        for t in self.transitions[current_state]:
            if t.action == action:
                # Check approval requirement
                if t.requires_approval and not approved:
                    return False
                
                # Execute transition
                old_state = task.state
                task.state = t.to_state.value
                
                # Trigger callbacks
                self._trigger_callbacks(task, old_state, t.to_state.value, action)
                return True
        
        return False
    
    def get_available_actions(self, task) -> List[Dict]:
        """Get available actions for current state"""
        current_state = task.state
        if current_state not in self.transitions:
            return []
        
        actions = []
        for t in self.transitions[current_state]:
            actions.append({
                "action": t.action,
                "to_state": t.to_state.value,
                "requires_approval": t.requires_approval,
            })
        return actions
    
    def on_transition(self, from_state: str, to_state: str, callback: Callable):
        """Register callback for specific transition"""
        key = f"{from_state}->{to_state}"
        if key not in self.callbacks:
            self.callbacks[key] = []
        self.callbacks[key].append(callback)
    
    def _trigger_callbacks(self, task, from_state: str, to_state: str, action: str):
        """Trigger registered callbacks"""
        key = f"{from_state}->{to_state}"
        if key in self.callbacks:
            for callback in self.callbacks[key]:
                try:
                    callback(task, from_state, to_state, action)
                except Exception:
                    pass


class WorkflowEngine:
    """Execute workflows based on state transitions"""
    
    def __init__(self, state_machine: StateMachine):
        self.state_machine = state_machine
        self.workflows: Dict[str, List[Callable]] = {}
    
    def register_workflow(self, trigger: str, steps: List[Callable]):
        """Register workflow for trigger"""
        self.workflows[trigger] = steps
    
    async def execute(self, trigger: str, task, context: dict = None):
        """Execute workflow"""
        if trigger not in self.workflows:
            return
        
        for step in self.workflows[trigger]:
            try:
                await step(task, context)
            except Exception as e:
                print(f"Workflow step failed: {e}")
                break
