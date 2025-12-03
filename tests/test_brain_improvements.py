import sys
import os
import unittest
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

from jarvis.core.brain import Brain

class TestBrainImprovements(unittest.TestCase):
    def setUp(self):
        self.brain = Brain()
        # Mock the LLM to avoid actual API calls and test logic
        self.brain.llm = MagicMock()
        self.brain.llm.chat_with_context = MagicMock()

    def test_think_structure(self):
        """Test that think method constructs the prompt correctly."""
        text = "Hello Jarvis"
        short_term = ["User: Hi", "Jarvis: Hello"]
        long_term = {"name": "Tony"}
        
        self.brain.think(text, short_term, long_term)
        
        # Verify call arguments
        args, _ = self.brain.llm.chat_with_context.call_args
        user_input, context, system_instruction = args
        
        self.assertEqual(user_input, text)
        self.assertIn("Recent conversation:", context)
        self.assertIn("User: Hi", context)
        self.assertIn("What I know about you:", context)
        self.assertIn("name: Tony", context)
        
        self.assertIn("You are Jarvis", system_instruction)
        self.assertIn("CORE INSTRUCTIONS", system_instruction)
        self.assertIn("Reactive TTS", system_instruction)
        self.assertIn("AVAILABLE ACTIONS", system_instruction)

    def test_think_no_memory(self):
        """Test think method without memory."""
        text = "Open camera"
        self.brain.think(text)
        
        args, _ = self.brain.llm.chat_with_context.call_args
        _, context, _ = args
        
        self.assertEqual(context, "")

if __name__ == '__main__':
    unittest.main()
