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
        print("Router: Cleaning up resources...")
        if hasattr(self, 'memory'):
            self.memory.prepare_for_exit()
        
        # Ensure Vision resources are released
        try:
            vision_actions.close_camera()
        except:
            pass

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
            
            # Vision Intents
            "VISION_OCR": vision_actions.read_text,
            "VISION_DESCRIBE": vision_actions.describe_scene,
            "VISION_OBJECTS": vision_actions.detect_objects,
            "VISION_PEOPLE": vision_actions.identify_people,
            "VISION_REPAIR": vision_actions.repair_vision_system,
            "VISION_LEARN_FACE": vision_actions.finalize_face_learning,
            "VISION_CLOSE": vision_actions.close_camera,
            "ADVANCED_SCENE_ANALYSIS": vision_actions.get_scene_context,
            "VISION_QR": vision_actions.scan_qr_code,
            "VISION_GESTURE": vision_actions.gesture_control,
            "VISION_EMOTION": vision_actions.detect_emotion,
            "VISION_POSTURE": vision_actions.check_posture,
            "VISION_RECORD": vision_actions.record_video,
            "VISION_DEEP_SCAN": vision_actions.deep_scan,
            "VISION_DOCUMENT": vision_actions.document_scan,
            "VISION_ACTIVITY": vision_actions.activity_recognition,
            "VISION_TRACK": vision_actions.object_tracking,
            "VISION_HIGHLIGHT": vision_actions.highlight_object,
            "SCREEN_OCR": vision_actions.read_screen,
            "SCREEN_DESCRIBE": vision_actions.describe_screen,

            # Web Intelligence
            "WEB_NEWS": web_actions.get_news,
            "WEB_WEATHER": web_actions.get_weather,
            "WEB_RESEARCH": web_actions.deep_research,

            # Task Management & Productivity
            "TASK_TIMER": lambda duration=None, **kwargs: productivity_actions.set_timer(
                (int(duration.split()[0]) * 60) if duration and "min" in duration else 
                (int(duration.split()[0]) if duration and duration.split()[0].isdigit() else 60)
            ),
            "TASK_REMINDER": productivity_actions.create_reminder,
            "TODO_ADD": productivity_actions.todo_add,
            "TODO_LIST": productivity_actions.todo_list,
            "TODO_DELETE": productivity_actions.todo_delete,
            "DOC_SUMMARIZE": productivity_actions.summarize_document,
            "DOC_ASK": productivity_actions.ask_about_document,
            "CODE_EXPLAIN": productivity_actions.explain_code,
            "PROJECT_ANALYZE": productivity_actions.analyze_project,

            # Connectivity & System Extras
            "SYSTEM_RECYCLE_BIN": system_actions.empty_recycle_bin,
            "SYSTEM_WIFI_CONNECT": system_actions.connect_wifi,
            "SYSTEM_WIFI_DISCONNECT": system_actions.disconnect_wifi,
            "SYSTEM_BLUETOOTH": system_actions.toggle_bluetooth,
            "SYSTEM_HOTSPOT": system_actions.handle_hotspot,

            # File Operations - Previously Missing
            "FILE_SEARCH": file_actions.search_file,
            "FILE_CREATE": file_actions.create_file,

            # Media Control - Previously Missing
            "MEDIA_CONTROL": self._handle_media_control,

            # Vision Document Scan - Previously Missing
            "VISION_DOCUMENT": vision_actions.document_scan,

            # Task Management - Previously Missing
            "TASK_MANAGEMENT": productivity_actions.create_reminder,

            # Memory Intents - Wire to router handlers
            "MEMORY_WRITE": self._handle_memory_write,
            "MEMORY_READ": self._handle_memory_read,
            "MEMORY_FORGET": self._handle_memory_forget,
        }

    # --- Memory Handlers ---
    def _handle_memory_write(self, content=None, **kwargs):
        """Handle explicit memory write requests"""
        import re
        
        # Get full original text as fallback
        full_text = kwargs.get("text", "")
        
        # If content is weak (it/this/that), use full text instead
        weak_words = ["it", "this", "that", ""]
        if content and content.lower().strip() in weak_words:
            content = full_text
        
        if not content:
            content = full_text
        if not content:
            return "I didn't catch what you wanted me to remember."
        
        # Clean up the content - remove "Hey Jarvis" prefix and memorize suffix
        content = re.sub(r"^(?:hey\s+)?jarvis[,\s]*", "", content, flags=re.IGNORECASE)
        content = re.sub(r",?\s*(?:kindly\s+)?(?:memorize|remember)\s+(?:it|this|that)\.?$", "", content, flags=re.IGNORECASE)
        content = content.strip()
        
        content_lower = content.lower()

        
        # Check for relationship patterns and store directly
        relationship_patterns = [
            (r"(?:my\s+)?father(?:'s\s+name)?\s+is\s+(.+)", "father"),
            (r"(?:my\s+)?mother(?:'s\s+name)?\s+is\s+(.+)", "mother"),
            (r"(?:my\s+)?(?:girlfriend|gf)(?:'s\s+name)?\s+is\s+(.+)", "girlfriend"),
            (r"(?:my\s+)?(?:boyfriend|bf)(?:'s\s+name)?\s+is\s+(.+)", "boyfriend"),
            (r"(?:my\s+)?(?:wife|spouse)(?:'s\s+name)?\s+is\s+(.+)", "wife"),
            (r"(?:my\s+)?husband(?:'s\s+name)?\s+is\s+(.+)", "husband"),
            (r"(?:my\s+)?brother(?:'s\s+name)?\s+is\s+(.+)", "brother"),
            (r"(?:my\s+)?sister(?:'s\s+name)?\s+is\s+(.+)", "sister"),
            (r"(?:my\s+)?friend(?:'s\s+name)?\s+is\s+(.+)", "friend"),
        ]
        
        for pattern, rel_type in relationship_patterns:
            match = re.search(pattern, content_lower)
            if match:
                name = match.group(1).strip().title()
                # Store in relationships
                if "relationships" not in self.memory.long_term:
                    self.memory.long_term["relationships"] = {}
                self.memory.long_term["relationships"][name] = {
                    "type": rel_type,
                    "details": f"User's {rel_type}",
                    "last_interaction": __import__("datetime").datetime.now().isoformat()
                }
                self.memory.save_memory()
                return f"I've memorized that your {rel_type}'s name is {name}."
        
        # Check for birthday pattern
        birthday_match = re.search(r"(?:my\s+)?birthday\s+is\s+(.+)", content_lower)
        if birthday_match:
            birthday = birthday_match.group(1).strip()
            if "personal_history" not in self.memory.long_term:
                self.memory.long_term["personal_history"] = []
            # Update or add birthday
            for event in self.memory.long_term["personal_history"]:
                if event.get("type") == "birthday":
                    event["description"] = f"My birthday is {birthday}"
                    self.memory.save_memory()
                    return f"Updated your birthday to {birthday}."
            self.memory.long_term["personal_history"].append({
                "type": "birthday",
                "description": f"My birthday is {birthday}",
                "date": birthday
            })
            self.memory.save_memory()
            return f"I've memorized that your birthday is {birthday}."
        
        # Default: use memory_manager for general facts
        try:
            from .memory.entries import MemoryType
            result = self.memory_manager.propose_write(content, MemoryType.LONG_TERM, confidence=1.0)
            return result.get("message", f"Memorized: {content}")
        except Exception as e:
            # Fallback: store in general facts
            if "facts" not in self.memory.long_term:
                self.memory.long_term["facts"] = {"general": []}
            self.memory.long_term["facts"]["general"].append(content)
            self.memory.save_memory()
            return f"I've memorized: {content}"


    def _handle_memory_read(self, query=None, **kwargs):
        """Handle memory retrieval requests"""
        if not query: 
            query = kwargs.get("text", "")
        if not query:
            return "What do you want me to recall?"
        
        query_lower = query.lower()
        
        # Check for relationship queries first (most common)
        if "relationship" in query_lower or "father" in query_lower or "mother" in query_lower or "friend" in query_lower or "girlfriend" in query_lower or "brother" in query_lower or "sister" in query_lower:
            # Search in relationships from memory.json
            for name, info in self.memory.long_term.get("relationships", {}).items():
                rel_type = info.get("type", "").lower()
                if rel_type in query_lower or name.lower() in query_lower:
                    return f"Your {rel_type} is {name}. {info.get('details', '')}"
        
        # Check for event queries (birthday, anniversary, etc.)
        if "event" in query_lower or "birthday" in query_lower or "anniversary" in query_lower:
            for event in self.memory.long_term.get("personal_history", []):
                if event.get("type", "").lower() in query_lower or any(word in event.get("description", "").lower() for word in query_lower.split()):
                    return f"Your {event.get('type', 'event')}: {event.get('description')} on {event.get('date', 'unknown date')}"
        
        # Try semantic search via memory_manager
        try:
            results = self.memory_manager.retrieve(query)
            if results:
                top = results[0]
                return f"I remember: {top.content}"
        except Exception as e:
            print(f"Memory search error: {e}")
        
        # Fallback: check user_info
        user_info = self.memory.long_term.get("user_info", {})
        for key, val in user_info.items():
            if key.lower() in query_lower:
                return f"Your {key} is {val}"
        
        return f"I couldn't recall anything about '{query}'."


    def _handle_memory_forget(self, content=None, **kwargs):
        """Handle forget requests"""
        target = content
        if not target: return "What should I forget?"
        return f"I will forget about '{target}'. (Implementation pending integration)"

    def _handle_media_control(self, **kwargs):
        """Handle media control intents - routes to appropriate media action"""
        command = kwargs.get("command", "").lower()
        text = kwargs.get("text", "").lower()
        
        # Check both command slot and original text for keywords
        combined = f"{command} {text}"
        
        if "stop" in combined:
            return media_actions.stop_music()
        if "pause" in combined:
            return media_actions.pause_music()
        if "next" in combined or "skip" in combined:
            return media_actions.next_track()
        if "previous" in combined or "prev" in combined or "back" in combined:
            return media_actions.previous_track()
        if "play" in combined or "resume" in combined:
            return media_actions.play_music()
        
        # Default to toggle play/pause
        return media_actions.play_music()


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
        # UNIFIED INTENT ROUTING (Single classification pass with slots)
        # -----------------------------------------------------------------
        from .nlu.intent_classifier import get_classifier
        from .context_manager import get_context_manager
        
        classifier = get_classifier()
        ctx = get_context_manager()
        
        # 1. Classify - IntentClassifier now returns complete intent with slots
        intent_result = classifier.classify(text)
        intent_type = intent_result.get("intent", "CONVERSATION")
        confidence = intent_result.get("confidence", 0.0)
        slots = intent_result.get("slots", {})
        
        print(f"Router: Classified as {intent_type} (conf: {confidence:.2f}) with slots: {slots}")
        
        # 2. Update Context
        ctx.update_dialogue(text, "", intent_type, confidence)
        
        # 3. Execution Logic
        if intent_type in ["CHAT", "CONVERSATION", "UNKNOWN"]:
            # Fallback to LLM (Brain) for conversational responses
            llm_response = self.brain.think(text, self.memory.short_term, self.memory.long_term)
            try:
                clean = llm_response.replace("```json", "").replace("```", "").strip()
                if clean.startswith("{"):
                    response_data = json.loads(clean)
                else:
                    response_data = {"action": "speak", "text": clean}
            except:
                response_data = {"action": "speak", "text": llm_response}
        else:
            # Execute Specific Intent - slots already extracted by IntentClassifier
            intent_result["original_text"] = text
            
            res = self._handle_intent_object(intent_result)
            
            # Handle complex results (Summarization)
            if isinstance(res, dict) and res.get("needs_summary"):
                print("Generating conversational response for complex Intent result...")
                final_reply = self.brain.process_action_results(text, [{"action": res.get("action", intent_type), "result": res.get("result")}])
                
                ctx.update_dialogue(text, final_reply, intent_type, confidence)
                self.memory.remember_conversation(text, final_reply)
                return {"text": final_reply}
            
            # Handle direct results
            if isinstance(res, dict) and "text" in res:
                ctx.update_dialogue(text, res["text"], intent_type, confidence)
                self.memory.remember_conversation(text, res["text"])

            return res
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
        
        # Optimization: If it was a vision result but simple (e.g. success/fail), 
        # append it directly if it's not already there.
        if results and any(r.get("action") in data_intensive_actions for r in results):
             for r in results:
                 res_val = r.get("result")
                 if isinstance(res_val, str) and res_val not in action_summary:
                     action_summary += f" {res_val}"

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
                kwargs = {**slots}
                if "original_text" in intent_data:
                    kwargs["text"] = intent_data["original_text"]
                
                print(f"Executing Intent {intent_type} with slots {slots}")
                res = func(**kwargs)
                
                # Determine if we need to return a technical dict or a spoken message
                message = ""
                if isinstance(res, dict):
                    message = res.get("message") or res.get("text") or str(res)
                else:
                    message = str(res)

                # Flag for Router.route to know if this needs a 2nd turn
                data_intensive = ["VISION_OCR", "VISION_DESCRIBE", "VISION_OBJECTS", "VISION_PEOPLE", "SCREEN_OCR", "SCREEN_DESCRIBE"]
                needs_summary = intent_type in data_intensive or (isinstance(res, dict) and len(str(res)) > 100)

                return {
                    "text": message, 
                    "action": intent_type,
                    "result": res,
                    "needs_summary": needs_summary
                }
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
