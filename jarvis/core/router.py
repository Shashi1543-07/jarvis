import json
import inspect
import datetime
from core.brain import Brain
from core.memory import Memory

# Import all action modules
from actions import (
    system_actions, web_actions, media_actions, file_actions,
    app_actions, input_actions, productivity_actions, info_actions,
    comms_actions, ai_actions, memory_actions, vision_actions, meta_actions
)

class Router:
    def __init__(self):
        self.brain = Brain()
        self.memory = Memory()
        self.action_map = self._build_action_map()
        print("Router initialized with dynamic action dispatch.")

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

    def route(self, text):
        print(f"User Input: {text}")
        llm_response = self.brain.think(text, self.memory.short_term, self.memory.long_term)
        
        try:
            clean_response = llm_response.replace("```json", "").replace("```", "").strip()
            print(f"DEBUG: Raw LLM Response: {clean_response}")
            if not clean_response.startswith("{"):
                response_data = {"action": "speak", "text": clean_response}
            else:
                response_data = json.loads(clean_response)
        except json.JSONDecodeError:
            print(f"Error parsing JSON: {llm_response}")
            response_data = {"action": "speak", "text": "I'm having trouble thinking clearly."}
        
        reply_text = response_data.get("text", "")
        
        # 1. Update Memory
        self.memory.remember_context(f"User: {text}")
        if reply_text:
            self.memory.remember_context(f"Jarvis: {reply_text}")

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

        # 4. Decision: Second Turn / Conversational Bridge
        # We skip the second turn ONLY if there are no results needing explanation
        # and we already have a substantial reply.
        data_intensive_actions = ["describe_scene", "read_text", "detect_objects", "detect_handheld_object", "identify_people", "who_is_in_front", "analyze_screen", "read_screen"]
        
        needs_second_turn = False
        if results:
            # If any result comes from a data-intensive action, we MUST describe it
            if any(r.get("action") in data_intensive_actions for r in results):
                needs_second_turn = True
            # Or if the result actually contains data (not just "Success")
            elif any(isinstance(r.get("result"), (dict, list)) for r in results):
                needs_second_turn = True
        
        if not needs_second_turn and reply_text:
            return {"text": reply_text}

        # Call Brain to process results into natural language
        if results or not reply_text:
            print("Generating conversational response for action results...")
            final_reply = self.brain.process_action_results(text, results)
            return {"text": final_reply}
            
        return {"text": reply_text}

    def _log_action(self, action, params, result):
        try:
            with open("jarvis_actions.log", "a", encoding="utf-8") as f:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{ts}] {action} | Params: {params} | Result: {result}\n")
        except:
            pass
