import sys
import os
import unittest
import shutil
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

from core.memory.manager import MemoryManager
from core.memory.entries import MemoryType, MemorySource
from core.router import Router
from core.nlu.engine import NLUEngine
from core.nlu.intents import Intent, IntentType

class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.getcwd(), 'tests', 'test_config')
        os.makedirs(self.test_dir, exist_ok=True)
        self.manager = MemoryManager(config_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_write_validation(self):
        # 1. Reject Short Content
        res = self.manager.propose_write("Hi", MemoryType.SHORT_TERM, 0.9)
        self.assertFalse(res["success"])
        
        # 2. Reject PII
        res = self.manager.propose_write("My password is secret123", MemoryType.LONG_TERM, 0.9)
        self.assertFalse(res["success"])
        self.assertIn("PII", res["message"])
        
        # 3. Reject Low Confidence
        res = self.manager.propose_write("Maybe I like blue", MemoryType.LONG_TERM, 0.3)
        self.assertFalse(res["success"])
        
        # 4. Accept Valid
        res = self.manager.propose_write("My favorite color is blue", MemoryType.LONG_TERM, 0.95)
        self.assertTrue(res["success"])

    def test_retrieval(self):
        # Write
        self.manager.propose_write("Meeting at 3PM", MemoryType.LONG_TERM, 1.0)
        
        # Retrieve
        results = self.manager.retrieve("Meeting")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].content, "Meeting at 3PM")

class TestMemoryRouterIntegration(unittest.TestCase):
    def setUp(self):
        self.router = Router()
        # Mock MemoryManager to avoid filesystem
        self.router.memory_manager = MagicMock()
        self.router.memory_manager.propose_write.return_value = {"success": True, "message": "Saved."}
        self.router.memory_manager.retrieve.return_value = [MagicMock(content="Mock Memory")]

    def test_memory_write_intent(self):
        intent = {
            "intent": "MEMORY_WRITE",
            "slots": {"content": "I love Python"},
            "requires_confirmation": False
        }
        res = self.router._handle_intent_object(intent)
        
        self.router.memory_manager.propose_write.assert_called()
        self.assertEqual(res["text"], "Saved.")

    def test_memory_read_intent(self):
        intent = {
            "intent": "MEMORY_READ",
            "slots": {"query": "What do I love?"},
            "requires_confirmation": False
        }
        res = self.router._handle_intent_object(intent)
        
        self.router.memory_manager.retrieve.assert_called_with("What do I love?")
        self.assertIn("Mock Memory", res["text"])

if __name__ == '__main__':
    unittest.main()
