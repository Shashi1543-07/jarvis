import json
import re
from typing import Optional, List
from .schemas import ExecutionPlan, PlanStep, PlanType, StepAction
from ..ollama_brain import OllamaBrain

class PlannerEngine:
    """
    Core Logic for Multi-Step Planning.
    Uses LLM to decompose high-level commands into ExecutionPlans.
    """
    def __init__(self, llm_brain=None):
        self.llm = llm_brain or OllamaBrain()
        
    def should_plan(self, text: str) -> bool:
        """
        Heuristic check: Does this command look like it needs a plan?
        """
        # 1. Keywords indicating sequence
        triggers = [" and ", " then ", " after ", " before ", " -> ", " until ", " while "]
        if any(t in text.lower() for t in triggers):
            return True
            
        # 2. Complexity check (number of distinct verbs/actions?)
        # Simple heuristic: lengthy command with multiple action verbs
        action_verbs = ["open", "search", "create", "delete", "write", "check", "run", "calculate", "find", "play"]
        count = sum(1 for v in action_verbs if v in text.lower())
        if count >= 2:
            return True
            
        return False

    def generate_plan(self, user_command: str) -> ExecutionPlan:
        """
        Generate a structured execution plan from user command.
        """
        system_prompt = (
            "You are the Multi-Step Command Planner for JARVIS AI.\n"
            "Your goal is to decompose a complex User Command into a sequential List of Steps.\n"
            "Output VALID JSON only. No prose.\n"
            "\n"
            "Available Actions:\n"
            "- TOOL_CALL: Execute a system tool.\n"
            "- MOUSE_CLICK: Click at coordinates or use current position.\n"
            "- KEYBOARD_TYPE: Type a string.\n"
            "- KEYBOARD_PRESS: Press a specific key (e.g. 'enter', 'tab').\n"
            "- MOUSE_MOVE: Move to coordinates.\n"
            "- ASK_USER: Ask for clarification.\n"
            "\n"
            "Available Tools (for TOOL_CALL):\n"
            "- SYSTEM_OPEN_APP (input: app_name or URL)\n"
            "- SYSTEM_CLOSE_APP (input: app_name)\n"
            "- BROWSER_SEARCH (input: query)\n"
            "- SYSTEM_CONTROL (input: command like 'increase volume')\n"
            "- CLICK_ON_TEXT (input: exact text to find and click on screen)\n"
            "- TYPE_AT_TEXT (input: object {target: 'text to click', text: 'text to type'})\n"
            "- ACTION_REQUEST (input: generic action)\n"
            "\n"
            "Automation Rules:\n"
            "1. To search on a specific site (like YouTube): \n"
            "   Step 1: TOOL_CALL 'SYSTEM_OPEN_APP' with 'https://www.youtube.com'\n"
            "   Step 2: TOOL_CALL 'TYPE_AT_TEXT' with {target: 'Search', text: 'query'}\n"
            "   Step 3: KEYBOARD_PRESS 'enter' (optional if TYPE_AT_TEXT already does it)\n"
            "2. For creating content in a new local app (like Notepad):\n"
            "   Step 1: TOOL_CALL 'SYSTEM_OPEN_APP' with 'notepad'\n"
            "   Step 2: KEYBOARD_TYPE 'content' (Direct typing is safer for new blank windows)\n"
            "3. If coordinates are unknown, use CLICK_ON_TEXT to interact with UI elements by their label.\n"
            "\n"
            "Output Schema (JSON):\n"
            "{\n"
            "  \"description\": \"High level goal\",\n"
            "  \"plan_type\": \"linear\",\n"
            "  \"steps\": [\n"
            "    {\n"
            "      \"step_id\": 1,\n"
            "      \"description\": \"What this step does\",\n"
            "      \"action\": \"TOOL_CALL\" | \"MOUSE_CLICK\" | \"KEYBOARD_TYPE\" | \"KEYBOARD_PRESS\",\n"
            "      \"tool\": \"TOOL_NAME or null\",\n"
            "      \"input\": \"string or object {x, y, button, key}\",\n"
            "      \"depends_on\": null\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )

        response = self.llm.generate_response(f"User Command: {user_command}", system=system_prompt)
        
        try:
            # Clean JSON
            clean_json = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            # Construct Plan Object
            plan = ExecutionPlan(
                description=data.get("description", "Auto-generated plan"),
                plan_type=PlanType(data.get("plan_type", "linear"))
            )
            
            steps = []
            for s in data.get("steps", []):
                # Map action string to Enum
                action_str = s.get("action", "TOOL_CALL")
                try:
                    action_enum = StepAction(action_str)
                except:
                    action_enum = StepAction.TOOL_CALL
                
                step = PlanStep(
                    step_id=s.get("step_id"),
                    description=s.get("description", ""),
                    action=action_enum,
                    tool=s.get("tool"),
                    input=s.get("input"),
                    depends_on=s.get("depends_on")
                )
                steps.append(step)
            
            plan.steps = steps
            return plan
            
        except Exception as e:
            print(f"Planner Error: {e}")
            # Fallback: Return a single step plan delegating to NLU/Router logic if parsing fails??
            # Or just return empty plan which Router handles as failure.
            return ExecutionPlan(description="Failed to parse plan")
