
import re
from typing import Dict, Any, Optional
from ..context_manager import get_context_manager
from .engine import NLUEngine
from .intents import IntentType

class IntentClassifier:
    """
    Unified Intent Classifier - Single source of truth for intent classification.
    
    Architecture:
    1. Uses NLUEngine for regex rules + LLM-based slot extraction
    2. Applies context-aware overrides (vision active, dialogue history)
    3. Returns complete intent dict with slots
    
    This replaces the fragmented 3-classifier system with one unified flow.
    """
    
    def __init__(self):
        self.context = get_context_manager()
        self.nlu_engine = NLUEngine()  # Core slot extraction engine
        
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify user input and extract slots in a single pass.
        
        Returns:
            Dict with keys: intent, confidence, slots, requires_confirmation, 
                            clarification_question, original_text
        """
        text_lower = text.lower().strip()
        
        # ---------------------------------------------------------
        # STEP 1: Get base classification from NLUEngine (regex + LLM)
        # ---------------------------------------------------------
        intent = self.nlu_engine.parse(text)
        result = intent.to_dict()
        
        # ---------------------------------------------------------
        # STEP 2: Apply context-aware overrides
        # ---------------------------------------------------------
        result = self._apply_context_overrides(result, text_lower)
        
        # ---------------------------------------------------------
        # STEP 3: Validate and normalize
        # ---------------------------------------------------------
        result = self._normalize_result(result)
        
        return result
    
    def _apply_context_overrides(self, result: Dict[str, Any], text_lower: str) -> Dict[str, Any]:
        """
        Apply context-aware intelligence on top of base classification.
        This handles cases where context changes the meaning of ambiguous queries.
        """
        current_intent = result.get("intent", "")
        
        # ---------------------------------------------------------
        # VISION CONTEXT OVERRIDE
        # If camera is active, bias ambiguous queries toward vision actions
        # ---------------------------------------------------------
        if self.context.vision.is_active:
            # Pronouns + question words when camera is on -> Vision
            pronouns = [" he", " she", " it", " that", " this", " they"]
            question_words = ["who", "what"]
            
            has_pronoun = any(p in text_lower for p in pronouns)
            has_question = any(q in text_lower for q in question_words)
            
            if has_pronoun and has_question:
                # Context-aware override to vision
                if "who" in text_lower:
                    result["intent"] = "VISION_PEOPLE"
                    result["confidence"] = 0.92
                    result["slots"]["prompt"] = result.get("original_text", text_lower)
                elif "what" in text_lower:
                    result["intent"] = "VISION_DESCRIBE"
                    result["confidence"] = 0.90
                    result["slots"]["prompt"] = result.get("original_text", text_lower)
        
        # ---------------------------------------------------------
        # DIALOGUE CONTEXT OVERRIDE
        # Handle follow-up questions that reference previous intent
        # ---------------------------------------------------------
        if current_intent in ["CONVERSATION", "UNKNOWN"]:
            last_intent = self.context.dialogue.last_intent
            
            # If last intent was vision and user says "again" or "more"
            if last_intent and "VISION" in last_intent:
                follow_up_words = ["again", "more", "another", "else"]
                if any(w in text_lower for w in follow_up_words):
                    result["intent"] = last_intent
                    result["confidence"] = 0.85
                    result["slots"]["prompt"] = "Continue from last result"
        
        return result
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure result has all required fields with proper types.
        """
        # Ensure slots is always a dict
        if "slots" not in result or result["slots"] is None:
            result["slots"] = {}
            
        # Normalize intent name (handle enum values vs strings)
        intent = result.get("intent", "UNKNOWN")
        if hasattr(intent, 'value'):
            result["intent"] = intent.value
        elif isinstance(intent, str):
            result["intent"] = intent.upper()
        
        # GRACEFUL DEGRADATION: Convert UNKNOWN to CONVERSATION
        # This ensures unmatched queries fallback to LLM chat gracefully
        if result["intent"] == "UNKNOWN":
            result["intent"] = "CONVERSATION"
            result["confidence"] = 0.5  # Low confidence for fallback
            
        # Ensure confidence is a float
        result["confidence"] = float(result.get("confidence", 0.0))
        
        # Ensure boolean fields exist
        result["requires_confirmation"] = bool(result.get("requires_confirmation", False))
        
        return result


# Singleton accessor - returns fresh instance each time for context updates
_classifier_instance = None

def get_classifier() -> IntentClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier()
    return _classifier_instance
