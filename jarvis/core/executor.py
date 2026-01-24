import time
import os
import sys

# Ensure project root is in path for dynamic imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from .planner.schemas import ExecutionPlan, PlanStep, StepAction
from .os.input_controller import InputController
from .os.system_control import SystemControlManager
from .os.safety import PermissionGate, PermissionLevel, EmergencyStop

class Executor:
    """
    Deterministic execution engine for Plans.
    """
    def __init__(self):
        self.input_ctrl = InputController()
        self.sys_ctrl = SystemControlManager()
        self.gate = PermissionGate()
        
    def execute_plan(self, plan: ExecutionPlan):
        """Execute a plan step-by-step with safety checks."""
        print(f"Executor: Starting Plan {plan.plan_id}")
        results = []
        
        try:
            for step in plan.steps:
                # 1. Global Safety Check
                if EmergencyStop.is_set():
                    return {"status": "STOPPED", "message": "Emergency Stop Triggered"}
                
                print(f"Executor: Running Step {step.step_id} - {step.description}")
                
                # 2. Execute Step
                step_result = self._execute_step(step)
                results.append(f"Step {step.step_id}: {step_result}")
                
                # Small delay between steps
                time.sleep(0.5)
                
            return {"status": "COMPLETED", "message": "\n".join(results)}
            
        except KeyboardInterrupt:
            return {"status": "STOPPED", "message": "User Interrupt"}
        except Exception as e:
            print(f"Executor Error: {e}")
            return {"status": "ERROR", "message": str(e)}

    def _execute_step(self, step: PlanStep):
        """Internal logic for a single step"""
        # --- INPUT ACTIONS ---
        if step.action == StepAction.MOUSE_MOVE:
            if self.gate.check_permission(PermissionLevel.INPUT_EMULATION):
                input_data = step.input if isinstance(step.input, dict) else {}
                x = input_data.get("x", 0)
                y = input_data.get("y", 0)
                self.input_ctrl.mouse_move(x, y)
                return f"Mouse Moved to ({x}, {y})"

        elif step.action == StepAction.MOUSE_CLICK:
            if self.gate.check_permission(PermissionLevel.INPUT_EMULATION):
                input_data = step.input if isinstance(step.input, dict) else {}
                x = input_data.get("x") # Optional
                y = input_data.get("y") # Optional
                button = input_data.get("button", "left")
                self.input_ctrl.mouse_click(x, y, button=button)
                return f"Mouse Clicked {button} at ({x},{y})"

        elif step.action == StepAction.KEYBOARD_TYPE:
            if self.gate.check_permission(PermissionLevel.INPUT_EMULATION):
                text = step.input
                if isinstance(step.input, dict):
                    text = step.input.get("text", "")
                self.input_ctrl.keyboard_type(text)
                return f"Typed text: {text}"

        elif step.action == StepAction.KEYBOARD_PRESS:
            if self.gate.check_permission(PermissionLevel.INPUT_EMULATION):
                key = step.input
                if isinstance(step.input, dict):
                    key = step.input.get("key")
                self.input_ctrl.keyboard_press([key])
                return f"Pressed Key: {key}"

        # --- TOOL CALLS ---
        elif step.action == StepAction.TOOL_CALL:
            tool = step.tool
            val = step.input
            
            if tool == "SYSTEM_OPEN_APP":
                if self.gate.check_permission(PermissionLevel.SYSTEM_CONTROL):
                    success = self.sys_ctrl.open_app(val)
                    return f"Opened {val}" if success else f"Failed to open {val}"
            
            elif tool == "SYSTEM_CLOSE_APP":
                if self.gate.check_permission(PermissionLevel.SYSTEM_CONTROL):
                    success = self.sys_ctrl.close_app(val)
                    return f"Closed {val}" if success else f"Failed to close {val}"
                    
            elif tool == "BROWSER_SEARCH":
                if self.gate.check_permission(PermissionLevel.SYSTEM_CONTROL):
                    from jarvis.actions.web_actions import google_search
                    res = google_search(val)
                    return f"Search result: {res}"

            elif tool == "SYSTEM_CONTROL":
                if self.gate.check_permission(PermissionLevel.SYSTEM_CONTROL):
                    from jarvis.actions.system_actions import handle_system_control
                    res = handle_system_control(command=val)
                    return str(res)
            
            elif tool == "CLICK_ON_TEXT":
                if self.gate.check_permission(PermissionLevel.INPUT_EMULATION):
                    from jarvis.actions.input_actions import click_on_text
                    return click_on_text(val)

            elif tool == "TYPE_AT_TEXT":
                if self.gate.check_permission(PermissionLevel.INPUT_EMULATION):
                    from jarvis.actions.input_actions import type_at_text
                    # val might be a dict or comma string
                    if isinstance(val, dict):
                        target = val.get("target")
                        text = val.get("text")
                    else:
                        # Fallback for simple string if possible
                        target = val
                        text = "" 
                    return type_at_text(target, text)
            
            return f"Tool {tool} executed with input: {val}"

        return f"Unknown action type: {step.action}"

    def execute_single_action(self, action_type, **kwargs):
        """Direct execution for simple Intent -> Action mapping (Layer 1 bypass)"""
        # Used by Router for single-step intents ensuring they go through Safety
        
        if EmergencyStop.is_set(): return "Emergency Stop Active."
        
        if action_type == "SYSTEM_OPEN_APP":
             if self.gate.check_permission(PermissionLevel.SYSTEM_CONTROL):
                 self.sys_ctrl.open_app(kwargs.get("app_name"))
                 return f"Opening {kwargs.get('app_name')}"
        
        return "Action Executed via Executor"
