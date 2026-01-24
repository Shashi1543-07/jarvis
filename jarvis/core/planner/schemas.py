from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid

class PlanType(Enum):
    LINEAR = "linear"
    CONDITIONAL = "conditional"
    LOOP = "loop"

class StepAction(Enum):
    TOOL_CALL = "TOOL_CALL"
    CHECK_CONDITION = "CHECK_CONDITION"
    WAIT = "WAIT"
    ASK_USER = "ASK_USER"
    MEMORY_WRITE_PROPOSAL = "MEMORY_WRITE_PROPOSAL"
    END_PLAN = "END_PLAN"
    
    # Explicit Input Actions
    MOUSE_MOVE = "MOUSE_MOVE"
    MOUSE_CLICK = "MOUSE_CLICK"
    KEYBOARD_TYPE = "KEYBOARD_TYPE"
    KEYBOARD_PRESS = "KEYBOARD_PRESS"

@dataclass
class PlanStep:
    step_id: int
    description: str
    action: StepAction
    tool: Optional[str] = None
    input: Optional[Any] = None
    depends_on: Optional[int] = None
    
    # Using dict for flexibility with conditionals/loops which might have complex logic
    # but primarily mapping to the prompt requirements
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "step_id": self.step_id,
            "description": self.description,
            "action": self.action.value,
            "tool": self.tool,
            "input": self.input,
            "depends_on": self.depends_on,
            **self.metadata
        }

@dataclass
class ExecutionPlan:
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    plan_type: PlanType = PlanType.LINEAR
    multi_step: bool = True
    steps: List[PlanStep] = field(default_factory=list)
    interruptible: bool = True
    failure_policy: str = "STOP_AND_ASK_USER"
    
    def to_dict(self):
        return {
            "plan_id": self.plan_id,
            "description": self.description,
            "plan_type": self.plan_type.value,
            "multi_step": self.multi_step,
            "steps": [s.to_dict() for s in self.steps],
            "interruptible": self.interruptible,
            "failure_policy": self.failure_policy
        }
