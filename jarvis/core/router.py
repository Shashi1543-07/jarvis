import json
import inspect
import datetime
import atexit
from .brain import Brain
from .enhanced_memory import EnhancedMemory

# Import all action modules
from actions import (
    system_actions, web_actions, media_actions, file_actions,
    app_actions, input_actions, productivity_actions, info_actions,
    comms_actions, ai_actions, memory_actions, vision_actions, meta_actions
)

class Router:
    def __init__(self):
        self.memory = EnhancedMemory() # Keep for legacy, but transition to Manager
        from .memory.manager import MemoryManager
        self.memory_manager = MemoryManager()
        
        # Initialize Planner & Executor
        from .planner.engine import PlannerEngine
        from .executor import Executor
        self.planner = PlannerEngine()
        self.executor = Executor()
        
        self.brain = Brain(self.memory) # Share common memory instance
        self.action_map = self._build_action_map()
        
        # New Intent Support
        self.pending_intent = None  # Store intent requiring confirmation
        self.intent_map = self._build_intent_map()
        
        # GUI callback for intent classification
        self.on_intent_classified = None
        
        # Connect brain's classification to router's callback
        self.brain.on_intent_classified = lambda intent, conf: self.on_intent_classified(intent, conf) if self.on_intent_classified else None
        
        print("Router initialized with dynamic action dispatch and Intent System.")

        # Register exit handler to clear temporary memory
        atexit.register(self._cleanup_on_exit)

    def _cleanup_on_exit(self):
        """Cleanup function called when the program exits"""
        if hasattr(self, 'memory'):
            self.memory.prepare_for_exit()

    def _build_action_map(self):
        modules = [
            system_actions, web_actions, media_actions, file_actions,
            app_actions, input_actions, productivity_actions, info_actions,
            comms_actions, ai_actions, memory_actions, vision_actions, meta_actions
        ]
        action_map = {}
        for module in modules:
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if not name.startswith("_"):
                    action_map[name] = func
        return action_map

    def _build_intent_map(self):
        """Map Intent Strings to Action Functions"""
        return {
            "SYSTEM_OPEN_APP": app_actions.open_app,
            "SYSTEM_CLOSE_APP": app_actions.close_app,
            "SYSTEM_CONTROL": system_actions.handle_system_control, # Updated dispatcher
            "FILE_DELETE": file_actions.delete_file,
            "FILE_SEARCH": file_actions.search_file,
            "BROWSER_SEARCH": web_actions.google_search if hasattr(web_actions, 'google_search') else web_actions.open_website,
            
            # Semantic Memory Intents
            "MEMORY_WRITE": self._handle_memory_write,
            "MEMORY_READ": self._handle_memory_read,
            "MEMORY_FORGET": self._handle_memory_forget,
        }

    # --- Memory Handlers ---
    def _handle_memory_write(self, content=None, **kwargs):
        """Handle explicit memory write requests"""
        from .memory.entries import MemoryType
        if not content: return "I didn't catch what you wanted me to remember."
        
        # Determine strict intent from slot if possible, else LTM
        result = self.memory_manager.propose_write(content, MemoryType.LONG_TERM, confidence=1.0)
        return result["message"]

    def _handle_memory_read(self, query=None, **kwargs):
        """Handle memory retrieval requests"""
        if not query: return "What do you want me to recall?"
        results = self.memory_manager.retrieve(query)
        if results:
            # Format top result for speech
            top = results[0]
            return f"I remember: {top.content}"
        return f"I couldn't recall anything about '{query}'."

    def _handle_memory_forget(self, content=None, **kwargs):
        """Handle forget requests"""
        target = content
        if not target: return "What should I forget?"
        return f"I will forget about '{target}'. (Implementation pending integration)"

    def route(self, text):
        print(f"User Input: {text}")

        # Update personality profile based on recent interactions
        self.memory.analyze_personality()

        # -----------------------------------------------------------------
        # CONFIRMATION LOOP
        # -----------------------------------------------------------------
        if self.pending_intent:
            text_lower = text.lower()
            if any(w in text_lower for w in ["yes", "yeah", "do it", "confirm", "sure", "proceed"]):
                # User Confirmed
                print(f"DEBUG: User confirmed pending intent: {self.pending_intent}")
                intent_to_run = self.pending_intent
                self.pending_intent = None
                return self._execute_intent(intent_to_run)
            elif any(w in text_lower for w in ["no", "cancel", "don't", "stop", "abort"]):
                # User Cancelled
                self.pending_intent = None
                return {"text": "Cancelled.", "action": "speak"}
            self.pending_intent = None

        # -----------------------------------------------------------------
        # LAYER 0: MULTI-STEP PLANNER CHECK
        # -----------------------------------------------------------------
        if self.planner.should_plan(text):
            print("Router: Detected complex command. Invoking Planner...")
            plan = self.planner.generate_plan(text)
            print(f"Router: Plan Generated: {plan}")
            result = self.executor.execute_plan(plan)
            return {"text": f"Plan execution result: {result['message']}", "action": "PLAN_COMPLETE"}

        # -----------------------------------------------------------------
        # NORMAL NLU FLOW
        # -----------------------------------------------------------------
        llm_response = self.brain.think(text, self.memory.short_term, self.memory.long_term)

        try:
            clean_response = llm_response.replace("```json", "").replace("```", "").strip()
            # print(f"DEBUG: Raw LLM Response: {clean_response}")
            if not clean_response.startswith("{"):
                response_data = {"action": "speak", "text": clean_response}
            else:
                response_data = json.loads(clean_response)
                
            # Extract and emit intent if present
            if "intent" in response_data and self.on_intent_classified:
                intent_name = response_data["intent"]
                confidence = response_data.get("confidence", 0.9)
                try:
                    self.on_intent_classified(intent_name, confidence)
                except Exception as e:
                    print(f"Router: Failed to emit intent to GUI: {e}")
            
            # CHECK FOR NEW INTENT STRUCTURE WITH SLOTS
            if "intent" in response_data and "slots" in response_data:
                return self._handle_intent_object(response_data)
                    
        except json.JSONDecodeError:
            print(f"Error parsing JSON: {llm_response}")
            response_data = {"action": "speak", "text": "I'm having trouble thinking clearly."}

        # Fallback to Legacy Action-Dictionary Handling
        reply_text = response_data.get("text", "")

        # 1. Update Memory
        if reply_text:
            self.memory.remember_conversation(text, reply_text)
        else:
            self.memory.remember_context(f"User: {text}")

        # 2. Collect Actions
        actions_to_run = []
        if "actions" in response_data and isinstance(response_data["actions"], list):
            actions_to_run = response_data["actions"]
        elif "action" in response_data and response_data["action"] != "speak":
            # Extract params for single action
            if "params" in response_data:
                params = response_data["params"]
            else:
                params = {k: v for k, v in response_data.items() if k not in ["action", "text", "actions"]}
            actions_to_run = [{"action": response_data["action"], "params": params}]

        # 3. Execute Actions
        results = []
        for item in actions_to_run:
            name = item.get("action")
            params = item.get("params", {})
            if name in self.action_map:
                try:
                    print(f"Executing: {name} with params: {params}")
                    res = self.action_map[name](**params)
                    print(f"Result: {res}")
                    results.append({"action": name, "result": res})
                    self._log_action(name, params, res)
                except Exception as e:
                    print(f"Error executing {name}: {e}")
                    results.append({"action": name, "error": str(e)})
            else:
                print(f"Unknown action: {name}")

        # 4. Handle results and determine if second turn is needed
        # Aggressively skip second turn for routine actions to save quota.
        data_intensive_actions = ["describe_scene", "read_text", "detect_objects", "detect_handheld_object", "identify_people", "who_is_in_front", "analyze_screen", "read_screen", "google_search"]

        needs_second_turn = False
        action_summary = ""
        
        if results:
            for r in results:
                action_name = r.get("action")
                result_data = r.get("result")

                if action_name in data_intensive_actions:
                    needs_second_turn = True
                    break
                # If result is a complex object (dict/list) and not just a status string
                if isinstance(result_data, (dict, list)) and len(str(result_data)) > 50:
                    needs_second_turn = True
                    break
                
                # For simple string results (like battery status, volume result), collect them to append if no second turn
                if isinstance(result_data, str) and result_data:
                    if action_summary: action_summary += " "
                    action_summary += result_data

        if needs_second_turn:
            print("Generating conversational response for data-rich results...")
            final_reply = self.brain.process_action_results(text, results)
            # Update memory with final reply turn
            self.memory.remember_conversation(text, final_reply)
            return {"text": final_reply}

        # Final response construction
        final_text = reply_text if reply_text else "Action completed, sir."
        if action_summary and action_summary not in final_text:
            final_text += f" {action_summary}"
            
        # Check for behavior learning suggestions
        suggestions = self.brain.behavior_learning.suggest_based_on_patterns()
        if suggestions and "suggestion" in text.lower():
            suggestion_text = " ".join(suggestions[:1])
            final_text += f" By the way, {suggestion_text.lower()}"

        # Return action name of the first action for state machine triggers (like sleep)
        main_action = actions_to_run[0].get("action") if actions_to_run else None
        return {"text": final_text, "action": main_action}

    def _handle_intent_object(self, intent_data):
        intent_type = intent_data.get("intent")
        slots = intent_data.get("slots", {})
        requires_confirmation = intent_data.get("requires_confirmation", False)
        clarification_question = intent_data.get("clarification_question")

        # 1. Clarification Needed
        if intent_type == "CLARIFICATION_REQUIRED" and clarification_question:
            return {"text": clarification_question, "action": "speak"}
            
        # 2. Safety Confirmation
        # USER REQUEST: Only shutdown/restart should ask for confirmation.
        is_high_risk = any(kw in intent_type.lower() for kw in ["shutdown", "restart", "reboot"])
        
        if requires_confirmation and is_high_risk:
            self.pending_intent = intent_data
            target_name = slots.get("app_name") or slots.get("file_name") or "item"
            return {"text": f"This action requires confirmation. Are you sure you want to proceed with {intent_type} on {target_name}?", "action": "speak"}
            
        # 3. Execution (Skip confirmation for non-high-risk actions)
        return self._execute_intent(intent_data)

    def _execute_intent(self, intent_data):
        intent_type = intent_data.get("intent")
        slots = intent_data.get("slots", {})
        
        # Check Intent Map First
        if intent_type in self.intent_map:
            func = self.intent_map[intent_type]
            try:
                # Dynamic execution
                # We need to map slots to function arguments intelligently
                # For now, simplistic mapping: pass slots as kwargs
                kwargs = {**slots}
                if "original_text" in intent_data:
                    # Provide original text so handlers can extract tricky params themselves
                    kwargs["text"] = intent_data["original_text"]
                
                print(f"Executing Intent {intent_type} with slots {slots}")
                res = func(**kwargs)
                return {"text": str(res), "action": intent_type}
            except Exception as e:
                print(f"Error executing intent {intent_type}: {e}")
                return {"text": f"Error executing command: {e}", "action": "error"}
        
        if "text" in intent_data:
            return {"text": intent_data["text"], "action": "speak"}
            
        return {"text": "I understood the intent but don't have a handler for it yet.", "action": "speak"}        

    def _log_action(self, action, params, result):
        try:
            with open("jarvis_actions.log", "a", encoding="utf-8") as f:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{ts}] {action} | Params: {params} | Result: {result}\n")
        except:
            pass
