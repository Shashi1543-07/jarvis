import sys
import os
import unittest
import json
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

from core.planner.engine import PlannerEngine
from core.planner.schemas import PlanType, StepAction
from core.router import Router

class TestPlannerEngine(unittest.TestCase):
    def setUp(self):
        # Mock LLM to return a predefined plan for testing
        self.mock_llm = MagicMock()
        self.planner = PlannerEngine(llm_brain=self.mock_llm)

    def test_heuristics(self):
        self.assertTrue(self.planner.should_plan("open chrome and search for cats"))
        self.assertTrue(self.planner.should_plan("first do X, then do Y"))
        self.assertFalse(self.planner.should_plan("what is the time"))

    def test_plan_generation_mock(self):
        # Setup mock response
        mock_plan_json = """
        {
            "description": "Test Plan",
            "plan_type": "linear",
            "steps": [
                {"step_id": 1, "action": "TOOL_CALL", "tool": "SYSTEM_OPEN_APP", "input": "Chrome"},
                {"step_id": 2, "action": "TOOL_CALL", "tool": "BROWSER_SEARCH", "input": "cats", "depends_on": 1}
            ]
        }
        """
        self.mock_llm.generate_response.return_value = mock_plan_json
        
        plan = self.planner.generate_plan("Open Chrome and search for cats")
        
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(plan.steps[0].tool, "SYSTEM_OPEN_APP")
        self.assertEqual(plan.steps[1].action, StepAction.TOOL_CALL)

class TestPlannerIntegration(unittest.TestCase):
    def setUp(self):
        self.router = Router()
        # Mock internal planner to avoid real LLM calls during unit tests
        self.router.planner = MagicMock()
        self.router.planner.should_plan.return_value = False # Default off
        
        # Mock action functions
        self.mock_open = MagicMock()
        self.mock_search = MagicMock()
        self.router.intent_map["SYSTEM_OPEN_APP"] = self.mock_open
        self.router.intent_map["BROWSER_SEARCH"] = self.mock_search

    def test_router_delegates_to_planner(self):
        # 1. Setup Planner to say "YES"
        self.router.planner.should_plan.return_value = True
        
        # 2. Setup Planner to return a plan
        from core.planner.schemas import ExecutionPlan, PlanStep, StepAction, PlanType
        plan = ExecutionPlan(
            steps=[
                PlanStep(1, "Open App", StepAction.TOOL_CALL, "SYSTEM_OPEN_APP", "Notepad"),
                PlanStep(2, "Search", StepAction.TOOL_CALL, "BROWSER_SEARCH", "Python")
            ]
        )
        self.router.planner.generate_plan.return_value = plan
        
        # 3. Call Route
        self.router.route("Open Notepad and search Python")
        
        # 4. Verify Execution
        self.router.planner.should_plan.assert_called()
        self.router.planner.generate_plan.assert_called()
        self.mock_open.assert_called_with(app_name="Notepad")
        self.mock_search.assert_called_with(query="Python")

if __name__ == '__main__':
    unittest.main()
