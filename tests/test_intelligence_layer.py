
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis.core.nlu.intent_classifier import get_classifier
from jarvis.core.context_manager import get_context_manager

class TestIntelligenceLayer(unittest.TestCase):
    def setUp(self):
        self.classifier = get_classifier()
        self.context = get_context_manager()
        # Reset context
        self.context.vision.is_active = False
        self.context.vision.detected_people = []

    def test_vision_priority(self):
        """Test that detection triggers Vision intent"""
        text = "What do you see in front of you?"
        result = self.classifier.classify(text)
        print(f"Input: '{text}' -> Intent: {result['type']}")
        self.assertIn("VISION", result['type'])

    def test_vision_context_resolution(self):
        """Test 'Who is he?' routing based on camera state"""
        text = "Who is he?"
        
        # Case 1: Camera OFF
        self.context.vision.is_active = False
        res_off = self.classifier.classify(text)
        print(f"Camera OFF: '{text}' -> {res_off['type']}")
        self.assertEqual(res_off["type"], "CHAT") # Should default to chat/LLM
        
        # Case 2: Camera ON
        self.context.vision.is_active = True
        res_on = self.classifier.classify(text)
        print(f"Camera ON: '{text}' -> {res_on['type']}")
        self.assertIn("VISION", res_on["type"])

    def test_system_confirmation(self):
        """Test high-risk commands require confirmation"""
        text = "Shutdown the system"
        result = self.classifier.classify(text)
        print(f"Input: '{text}' -> Requires Confirmation: {result.get('requires_confirmation')}")
        self.assertEqual(result["type"], "SYSTEM_CONTROL")
        self.assertTrue(result.get("requires_confirmation", False))

if __name__ == '__main__':
    unittest.main()
