
import re
from typing import Dict, Any, Optional
from ..context_manager import get_context_manager

class IntentClassifier:
    """
    Advanced Intent Router implementing strict hierarchy:
    1. VISION (if context active or explicit trigger)
    2. DIALOGUE (follow-ups)
    3. SYSTEM (control)
    4. ACTION (apps/web)
    5. CHAT (fallback)
    """
    
    def __init__(self):
        self.context = get_context_manager()
        
    def classify(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower().strip()
        
        # ---------------------------------------------------------
        # 1. VISION LAYER (Highest Priority)
        # ---------------------------------------------------------
        vision_triggers = ["see", "look", "watch", "view", "camera", "eyes", "recognize", "identify", "detect", "read", "scan"]
        vision_queries = ["who is that", "what is that", "what do you see", "describe scene", "who is in front"]
        
        # Check explicit triggers OR active vision context with vague queries
        is_vision_trigger = any(w in text_lower for w in vision_triggers)
        is_vision_query = any(q in text_lower for q in vision_queries)
        
        # Context-aware override: "Who is he?" when camera is on -> Vision
        is_contextual_vision = False
        if self.context.vision.is_active:
            # If camera is on, "who is he", "what is this" should map to vision
            pronouns = [" he", " she", " it", " that", " this"]
            if any(p in text_lower for p in pronouns) and ("who" in text_lower or "what" in text_lower):
                 is_contextual_vision = True

        if is_vision_trigger or is_vision_query or is_contextual_vision:
            # Sub-classification for Vision
            if "read" in text_lower or "text" in text_lower:
                return {"type": "VISION_OCR", "confidence": 0.95}
            elif "who" in text_lower or "identify" in text_lower or "person" in text_lower:
                return {"type": "VISION_PEOPLE", "confidence": 0.95}
            elif "describe" in text_lower:
                return {"type": "VISION_DESCRIBE", "confidence": 0.95}
            elif "close" in text_lower or "stop" in text_lower or "off" in text_lower:
                return {"type": "VISION_CLOSE", "confidence": 1.0}
            else:
                 # Default to scene description or object detection
                return {"type": "VISION_DESCRIBE", "confidence": 0.9}

        # ---------------------------------------------------------
        # 2. DIALOGUE / CONTEXT LAYER
        # ---------------------------------------------------------
        # Check for clarification answers or follow-ups
        # (Simplified for now - can be expanded)
        
        # ---------------------------------------------------------
        # 3. SYSTEM LAYER
        # ---------------------------------------------------------
        if any(w in text_lower for w in ["shutdown", "restart", "reboot", "sleep"]):
             return {"type": "SYSTEM_CONTROL", "confidence": 0.9, "requires_confirmation": True}
             
        if "volume" in text_lower or "brightness" in text_lower:
             return {"type": "SYSTEM_CONTROL", "confidence": 0.95}

        # ---------------------------------------------------------
        # 4. ACTION LAYER
        # ---------------------------------------------------------
        if "open" in text_lower or "launch" in text_lower:
             return {"type": "SYSTEM_OPEN_APP", "confidence": 0.85}
             
        if "search" in text_lower or "google" in text_lower:
             return {"type": "BROWSER_SEARCH", "confidence": 0.9}

        # ---------------------------------------------------------
        # 5. CHAT FALLBACK
        # ---------------------------------------------------------
        return {"type": "CHAT", "confidence": 0.6}

# Singleton accessor
def get_classifier():
    return IntentClassifier()
