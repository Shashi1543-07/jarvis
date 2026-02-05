import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import datetime

@dataclass
class VisionContext:
    """Persistent state of what Jarvis can 'see'"""
    is_active: bool = False
    camera_index: int = -1
    last_frame_time: float = 0.0
    
    # Semantic understanding
    detected_objects: List[str] = field(default_factory=list)
    detected_people: List[str] = field(default_factory=list) # Names or "Unknown"
    scene_description: str = ""
    foreground_subject: str = "" # The main focus (person or object)
    
    # Raw data for recycling if needed
    last_raw_results: Dict[str, Any] = field(default_factory=dict)

    def update(self, result_type: str, data: Any):
        self.last_frame_time = time.time()
        
        if result_type == "camera_status":
            self.is_active = data.get("is_active", False)
            self.camera_index = data.get("index", -1)
            if not self.is_active:
                self.clear()
                
        elif result_type == "identify_people":
            # data is list of dicts: {name, confidence, location...}
            names = [p.get("name", "Unknown") for p in data if p.get("confidence", 0) > 0.4]
            self.detected_people = names
            if names:
                self.foreground_subject = names[0] # Assume first is primary for now
                
        elif result_type == "detect_objects":
            # data is usually a string message or list
            if isinstance(data, list):
                self.detected_objects = data
            elif isinstance(data, dict):
                 self.detected_objects = data.get("objects", [])

        elif result_type == "scene_description":
            self.scene_description = data.get("description", "")

    def clear(self):
        self.detected_objects = []
        self.detected_people = []
        self.scene_description = ""
        self.foreground_subject = ""
        self.last_raw_results = {}

    def get_summary(self) -> str:
        if not self.is_active:
            return "Camera is off."
        
        parts = []
        if self.detected_people:
            parts.append(f"People: {', '.join(self.detected_people)}")
        if self.detected_objects:
            parts.append(f"Objects: {', '.join(self.detected_objects[:5])}")
        if self.scene_description:
            parts.append(f"Scene: {self.scene_description}")
            
        return " | ".join(parts) if parts else "Camera is on, but I haven't analyzed the scene yet."

@dataclass
class DialogueContext:
    """Track conversation flow and intent history"""
    history: List[Dict] = field(default_factory=list) # Last N turns
    last_intent: str = "CHAT"
    last_intent_confidence: float = 0.0
    active_subject: Optional[str] = None # Entity being discussed (e.g. "Iron Man", "file.txt")
    
    # Task Tracking
    current_task: Optional[str] = None # e.g. "writing_email"
    task_slots: Dict[str, Any] = field(default_factory=dict) # Collected info for task
    
    def add_turn(self, user_text: str, agent_text: str, intent: str, confidence: float):
        self.history.append({
            "user": user_text,
            "agent": agent_text,
            "intent": intent,
            "timestamp": time.time()
        })
        if len(self.history) > 10:
            self.history.pop(0)
            
        self.last_intent = intent
        self.last_intent_confidence = confidence

    def set_subject(self, subject: str):
        self.active_subject = subject

    def clear_task(self):
        self.current_task = None
        self.task_slots = {}

class ContextManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContextManager, cls).__new__(cls)
            cls._instance.vision = VisionContext()
            cls._instance.dialogue = DialogueContext()
        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def update_vision(self, result_type: str, data: Any):
        self.vision.update(result_type, data)

    def update_dialogue(self, user_text: str, agent_text: str, intent: str, confidence: float):
        self.dialogue.add_turn(user_text, agent_text, intent, confidence)

    def get_context_string(self) -> str:
        """Get a string representation for LLM prompting"""
        v_summary = self.vision.get_summary()
        d_summary = f"Last Intent: {self.dialogue.last_intent}"
        if self.dialogue.active_subject:
            d_summary += f", Topic: {self.dialogue.active_subject}"
            
        return f"[VISION]: {v_summary}\n[CONTEXT]: {d_summary}"

# Global accessor
def get_context_manager():
    return ContextManager.get_instance()
