import sys
import os

# Add the project root to sys.path
# CWD is C:\Users\lenovo\OneDrive\Documents\JarvisAI
sys.path.append(os.getcwd())

from jarvis.core.llm import LLM
import unittest
from unittest.mock import MagicMock, patch

class TestLLMRotation(unittest.TestCase):
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_key_rotation_on_429(self, mock_model, mock_configure):
        # Mocking models
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance
        
        # Setup: 429 error on first call, Success on second call (after rotation)
        responses = [
            Exception("429 Quota exceeded"),
            MagicMock(text="Success response")
        ]
        
        # Mock chat.send_message
        mock_chat = MagicMock()
        mock_chat.send_message.side_effect = responses
        mock_instance.start_chat.return_value = mock_chat
        
        llm = LLM()
        # Initial key should be first key
        first_key = llm.key_manager.get_current_key()
        
        result = llm.chat_with_context("Hello", "Context")
        
        # Check if it eventually succeeded
        self.assertEqual(result, "Success response")
        
        # Check if KEY rotation happened (current_key_index should have incremented)
        # and current_model_index should be 0 because we reset it on key rotation
        self.assertEqual(llm.current_model_index, 0)
        self.assertNotEqual(llm.key_manager.get_current_key(), first_key)
        print(f"Verified key rotation: New key starts with {llm.key_manager.get_current_key()[:8]}")

if __name__ == '__main__':
    unittest.main()
