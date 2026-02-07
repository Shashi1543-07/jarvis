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
    
    # Vision
    VISION_DESCRIBE = "VISION_DESCRIBE"
    VISION_OCR = "VISION_OCR"
    VISION_OBJECTS = "VISION_OBJECTS"
    VISION_PEOPLE = "VISION_PEOPLE"
    VISION_REPAIR = "VISION_REPAIR"
    VISION_LEARN_FACE = "VISION_LEARN_FACE"
    VISION_CLOSE = "VISION_CLOSE"
    ADVANCED_SCENE_ANALYSIS = "ADVANCED_SCENE_ANALYSIS"
    VISION_QR = "VISION_QR"
    VISION_GESTURE = "VISION_GESTURE"
    VISION_EMOTION = "VISION_EMOTION"
    VISION_POSTURE = "VISION_POSTURE"
    VISION_RECORD = "VISION_RECORD"
    VISION_DEEP_SCAN = "VISION_DEEP_SCAN"
    VISION_DOCUMENT = "VISION_DOCUMENT"
    VISION_ACTIVITY = "VISION_ACTIVITY"
    VISION_TRACK = "VISION_TRACK"
    VISION_HIGHLIGHT = "VISION_HIGHLIGHT"
    
    # Screen Analysis
    SCREEN_OCR = "SCREEN_OCR"
    SCREEN_DESCRIBE = "SCREEN_DESCRIBE"

    # Web Intelligence
    WEB_NEWS = "WEB_NEWS"
    WEB_WEATHER = "WEB_WEATHER"
    WEB_RESEARCH = "WEB_RESEARCH"

    # Productivity
    TASK_TIMER = "TASK_TIMER"
    TASK_REMINDER = "TASK_REMINDER"
    TODO_ADD = "TODO_ADD"
    TODO_LIST = "TODO_LIST"
    TODO_DELETE = "TODO_DELETE"
    DOC_SUMMARIZE = "DOC_SUMMARIZE"
    DOC_ASK = "DOC_ASK"
    CODE_EXPLAIN = "CODE_EXPLAIN"
    PROJECT_ANALYZE = "PROJECT_ANALYZE"

    # Connectivity & System Extras
    SYSTEM_RECYCLE_BIN = "SYSTEM_RECYCLE_BIN"
    SYSTEM_WIFI_CONNECT = "SYSTEM_WIFI_CONNECT"
    SYSTEM_WIFI_DISCONNECT = "SYSTEM_WIFI_DISCONNECT"
    SYSTEM_BLUETOOTH = "SYSTEM_BLUETOOTH"
    SYSTEM_HOTSPOT = "SYSTEM_HOTSPOT"

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
