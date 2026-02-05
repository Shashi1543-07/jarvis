from .classifier import QueryClassifier
from .local_brain import LocalBrain
import json
import subprocess
import requests
import time
import datetime
from .briefing_manager import BriefingManager
from .enhanced_memory import EnhancedMemory # Changed to use enhanced memory
from .behavior_learning import BehaviorLearning

class Brain:
    def __init__(self, memory=None):
        self.classifier = QueryClassifier()
        self.memory = memory or EnhancedMemory() # Changed to use EnhancedMemory # Shared or new Memory instance
        self.local_brain = LocalBrain(self.memory) # Initialize LocalBrain with shared memory
        self.briefing_manager = BriefingManager(self.memory, self.local_brain.ollama)
        self.behavior_learning = BehaviorLearning(self.memory) # Initialize behavior learning
        
        # GUI callback for intent classification
        self.on_intent_classified = None
        
        print("Brain initialized with Local protocols.")

    def think(self, text, short_term_memory=None, long_term_memory=None):
        # local_brain is now initialized in __init__, so this check is no longer needed
        # if not self.local_brain:
        #     from core.memory import Memory
        #     self.local_brain = LocalBrain(Memory())

        # 1. Classify the user intent
        classification = self.classifier.classify(text)
        print(f"DEBUG: Intent Classified as: {classification}")
        
        # Emit classification to GUI if callback registered
        if self.on_intent_classified:
            try:
                # Use simple confidence based on classification type
                confidence = 0.95 if classification != "CHAT" else 0.75
                self.on_intent_classified(classification, confidence)
            except Exception as e:
                print(f"Brain: Failed to emit intent to GUI: {e}")

        # 2. Learn from this interaction
        self.behavior_learning.learn_from_interaction(text, "", datetime.datetime.now())

        # 3. Route everything to local brain (which handles templates + Ollama reasoning)
        local_response = self.local_brain.process(text, classification)

        # Ensure it's JSON for the router
        if isinstance(local_response, dict):
            if "action" not in local_response:
                local_response["action"] = "speak"

            # Handle briefing action directly
            if local_response.get("action") == "generate_daily_briefing":
                briefing = self.briefing_manager.generate_report()
                # Return a structured response for the briefing
                return json.dumps({"action": "speak", "text": briefing, "type": "briefing"})

            return json.dumps(local_response)
        return json.dumps({"action": "speak", "text": str(local_response)})

    def process_action_results(self, user_input, action_results):
        """Report action outcomes using local processing or local LLM."""
        if not action_results:
            return "Command completed, Sir."

        # Collect raw results and detect vision data
        messages = []
        vision_context = []
        
        # NEW: Context Manager Integration
        from .context_manager import get_context_manager
        ctx = get_context_manager()

        for r in action_results:
            action_name = r.get("action")
            res = r.get("result")

            # Feed to Context Manager
            if isinstance(res, dict) and "type" in res:
                 ctx.update_vision(res["type"], res)

            # Special handling for structured vision data
            if isinstance(res, dict) and "type" in res:
                # Update visual cache if local brain exists
                if self.local_brain:
                    self.local_brain.visual_cache[res["type"]] = res

                if res["type"] == "handheld_analysis":
                    vision_context.append(f"YOLO detected: {res.get('yolo_detections')}")
                    vision_context.append(f"BLIP Scene: {res.get('scene_description')}")
                elif res["type"] == "ocr_result":
                    vision_context.append(f"OCR Text: {res.get('text') or res.get('message')}")
                elif res["type"] == "screen_analysis":
                    vision_context.append(f"Screen Content: {res.get('text')}")
                elif res["type"] == "object_detection":
                    vision_context.append(f"Objects: {res.get('message')}")
                elif res["type"] == "scene_description":
                    vision_context.append(f"Scene: {res.get('description')}")
                elif res["type"] == "identify_people":
                    vision_context.append(f"People: {res.get('message')}")

            # Standard message collection
            if isinstance(res, dict):
                messages.append(res.get("message") or res.get("text") or str(res))
            elif isinstance(res, list):
                messages.append(", ".join(map(str, res)))
            else:
                messages.append(str(res))

        raw_summary = " ".join(messages)

        # Learn from this interaction outcome
        self.behavior_learning.learn_from_interaction(user_input, raw_summary, datetime.datetime.now())

        # If we have vision data or a complex result, use Ollama for a JARVIS-style summary
        if self.local_brain and hasattr(self.local_brain, 'ollama'):
            system_prompt = (
                "You are JARVIS, a direct and efficient assistant. "
                "Provide the answer as concisely as possible. "
                "Do NOT use filler, greetings, or conversational phrases. "
                "Just report the text or facts detected."
            )

            # Combine raw summary and visual context
            detail_for_llm = raw_summary
            if vision_context:
                detail_for_llm += "\nVisual Details:\n" + "\n".join(vision_context)

            # Inject active context
            detail_for_llm += f"\n{ctx.get_context_string()}"

            user_prompt = f"User said: {user_input}\nAction Results: {detail_for_llm}"

            ollama_summary = self.local_brain.ollama.generate_response(user_prompt, system=system_prompt)

            if "ERROR" not in ollama_summary and ollama_summary:
                return ollama_summary

        return raw_summary or "The action was successful, Sir."
