from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional

class IntentType(Enum):
    # System Control
    SYSTEM_CONTROL = "SYSTEM_CONTROL"
    SYSTEM_OPEN_APP = "SYSTEM_OPEN_APP"
    SYSTEM_CLOSE_APP = "SYSTEM_CLOSE_APP"
    
    # File Operations
    FILE_OPERATION = "FILE_OPERATION"
    FILE_DELETE = "FILE_DELETE"
    FILE_CREATE = "FILE_CREATE"
    FILE_SEARCH = "FILE_SEARCH"
    
    # Applications
    APPLICATION_ACTION = "APPLICATION_ACTION"
    BROWSER_SEARCH = "BROWSER_SEARCH"
    MEDIA_CONTROL = "MEDIA_CONTROL"
    
    # Memory
    MEMORY_WRITE = "MEMORY_WRITE"
    MEMORY_READ = "MEMORY_READ"
    MEMORY_FORGET = "MEMORY_FORGET"
    
    # Task Management
    TASK_MANAGEMENT = "TASK_MANAGEMENT" # Alarm, timer, reminder
    
    # Knowledge
    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"
    
    # Conversation
    CONVERSATION = "CONVERSATION"
    GREETING = "GREETING"
    
    # Emergency
    EMERGENCY = "EMERGENCY"
    
    # Meta
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    UNKNOWN = "UNKNOWN"

@dataclass
class Intent:
    intent_type: IntentType
    confidence: float
    slots: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    original_text: str = ""
    clarification_question: Optional[str] = None

    def to_dict(self):
        return {
            "intent": self.intent_type.value,
            "confidence": self.confidence,
            "slots": self.slots,
            "requires_confirmation": self.requires_confirmation,
            "clarification_question": self.clarification_question,
            "original_text": self.original_text
        }
