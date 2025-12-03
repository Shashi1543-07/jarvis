import json
import inspect
from core.brain import Brain
from core.memory import Memory

# Import all action modules
from actions import (
    system_actions,
    web_actions,
    media_actions,
    file_actions,
    app_actions,
    input_actions,
    productivity_actions,
    info_actions,
    comms_actions,
    ai_actions,
    memory_actions,
    ai_actions,
    memory_actions,
    vision_actions,
    meta_actions
)

class Router:
    def __init__(self):
        self.brain = Brain()
        self.memory = Memory()
        self.action_map = self._build_action_map()
        print("Router initialized with dynamic action dispatch.")

    def _build_action_map(self):
        """
        Dynamically builds a map of action names to functions from all imported modules.
        """
        modules = [
            system_actions, web_actions, media_actions, file_actions,
            app_actions, input_actions, productivity_actions, info_actions,
            comms_actions, ai_actions, memory_actions, vision_actions, meta_actions
        ]
        
        action_map = {}
        for module in modules:
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if not name.startswith("_"): # Ignore private functions
                    action_map[name] = func
        return action_map

    def route(self, text):
        # 1. Get response from Brain (LLM)
        print(f"User Input: {text}")
        llm_response = self.brain.think(text, self.memory.short_term, self.memory.long_term)
        
        # 2. Parse JSON
        try:
            # Clean up potential markdown code blocks
            clean_response = llm_response.replace("```json", "").replace("```", "").strip()
            print(f"DEBUG: Raw LLM Response: {clean_response}")
            
            # Handle plain text fallback (if LLM fails to output JSON)
            if not clean_response.startswith("{"):
                response_data = {"action": "speak", "text": clean_response}
            else:
                response_data = json.loads(clean_response)
                
        except json.JSONDecodeError:
            print(f"Error parsing JSON from LLM: {llm_response}")
            response_data = {"action": "speak", "text": "I'm having trouble processing that request."}
        
        action = response_data.get("action", "speak")
        reply_text = response_data.get("text", "")
        
        # Extract parameters
        if "params" in response_data:
            parameters = response_data["params"]
        else:
            parameters = {k: v for k, v in response_data.items() if k not in ["action", "text", "actions"]}
        
        print(f"DEBUG: Parameters: {parameters}")
        
        self.memory.remember_context(f"User: {text}")
        if reply_text:
            self.memory.remember_context(f"Jarvis: {reply_text}")
        
        # 3. Execute Action(s)
        
        # Handle Combo Commands (Multiple Actions)
        if "actions" in response_data and isinstance(response_data["actions"], list):
            results = []
            print(f"Executing COMBO COMMANDS ({len(response_data['actions'])} actions)")
            
            for i, action_item in enumerate(response_data["actions"]):
                act_name = action_item.get("action")
                act_params = action_item.get("params", {})
                
                if act_name in self.action_map:
                    try:
                        print(f"[{i+1}] Executing: {act_name} with params: {act_params}")
                        func = self.action_map[act_name]
                        res = func(**act_params)
                        print(f"Result: {res}")
                        results.append(str(res))
                    except Exception as e:
                        print(f"Error executing {act_name}: {e}")
                        results.append(f"Error in {act_name}: {e}")
                else:
                    print(f"Unknown action in combo: {act_name}")
            
            combined_result = "\n".join(results)
            return {"action": "combo", "text": reply_text, "result": combined_result}

        # Single Action Execution
        if action == "speak":
            return {"action": "speak", "text": reply_text}
            
        elif action in self.action_map:
            func = self.action_map[action]
            try:
                print(f"Executing action: {action} with params: {parameters}")
                result = func(**parameters)
                print(f"Action result: {result}")
                
                # Generate natural language response for the result
                if result is not None:
                    try:
                        new_reply = self.brain.process_action_result(text, action, result)
                        if new_reply:
                            reply_text = new_reply
                            print(f"Updated reply based on action result: {reply_text}")
                    except Exception as e:
                        print(f"Error generating result response: {e}")
                
                # Log to file
                import datetime
                try:
                    with open("jarvis_actions.log", "a", encoding="utf-8") as f:
                        f.write(f"\n{'='*60}\n")
                        f.write(f"{datetime.datetime.now()}: Executed {action}\n")
                        f.write(f"Parameters: {parameters}\n")
                        f.write(f"Result: {result}\n")
                        f.write(f"{'='*60}\n")
                except:
                    pass
                
                return {"action": action, "text": reply_text, "result": result}
            except TypeError as e:
                print(f"Parameter mismatch for {action}: {e}")
                return {"action": "error", "text": f"I couldn't execute that. {e}"}
            except Exception as e:
                print(f"Error executing {action}: {e}")
                return {"action": "error", "text": f"Something went wrong: {e}"}
        else:
            print(f"Unknown action: {action}")
            return {"action": "error", "text": f"I don't know how to {action}."}

    def _execute_action(self, intent, parameters):
        # Legacy method, keeping for safety but route() now handles execution directly
        pass
