import sys
import os
import unittest
from unittest.mock import MagicMock

# Adjust path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

from core.nlu.engine import NLUEngine
from core.nlu.intents import IntentType
from core.router import Router

class TestNLUEngine(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.nlu = NLUEngine(self.mock_llm)

    def test_rule_open_app(self):
        intent = self.nlu.parse("Open Chrome")
        self.assertEqual(intent.intent_type, IntentType.SYSTEM_OPEN_APP)
        self.assertEqual(intent.slots["app_name"], "chrome")
        self.assertFalse(intent.requires_confirmation)

    def test_rule_delete_file_confirmation(self):
        intent = self.nlu.parse("Delete my results.txt")
        self.assertEqual(intent.intent_type, IntentType.FILE_DELETE)
        self.assertEqual(intent.slots["file_name"], "results.txt")
        self.assertTrue(intent.requires_confirmation)

    def test_browser_search(self):
        intent = self.nlu.parse("Search for python tutorials in browser")
        self.assertEqual(intent.intent_type, IntentType.BROWSER_SEARCH)
        self.assertEqual(intent.slots["query"], "python tutorials")

class TestRouterConfirmation(unittest.TestCase):
    def setUp(self):
        self.router = Router()
        # Mock the brain to avoid real LLM calls
        self.router.brain = MagicMock()
        self.router.brain.think.return_value = "{}" # Default empty response
        
        # Mock action functions to verify execution
        self.mock_open_app = MagicMock()
        self.router.intent_map["SYSTEM_OPEN_APP"] = self.mock_open_app
        
        self.mock_delete_file = MagicMock()
        self.router.intent_map["FILE_DELETE"] = self.mock_delete_file

    def test_router_executes_safe_intent(self):
        # Simulator passing an intent object directly to handle_intent_object (bypassing brain parsing for this test)
        intent_data = {
            "intent": "SYSTEM_OPEN_APP",
            "slots": {"app_name": "notepad"},
            "requires_confirmation": False
        }
        
        result = self.router._handle_intent_object(intent_data)
        self.mock_open_app.assert_called_with(app_name="notepad")
        self.assertEqual(result["action"], "SYSTEM_OPEN_APP")

    def test_router_blocks_dangerous_intent(self):
        intent_data = {
            "intent": "FILE_DELETE",
            "slots": {"file_name": "important.doc"},
            "requires_confirmation": True
        }
        
        result = self.router._handle_intent_object(intent_data)
        
        # Should NOT execute
        self.mock_delete_file.assert_not_called()
        
        # Should return confirmation text
        self.assertIn("confirmation", result["text"])
        self.assertIsNotNone(self.router.pending_intent)

    def test_router_executes_after_confirmation(self):
        # 1. Setup pending intent
        self.router.pending_intent = {
            "intent": "FILE_DELETE",
            "slots": {"file_name": "important.doc"},
            "requires_confirmation": True
        }
        
        # 2. User confirms
        result = self.router.route("Yes, do it")
        
        # 3. Verify execution
        self.mock_delete_file.assert_called_with(file_name="important.doc")
        self.assertIsNone(self.router.pending_intent)

if __name__ == '__main__':
    unittest.main()
