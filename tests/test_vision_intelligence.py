
import sys
import os
from unittest.mock import MagicMock, patch

def test_intelligence():
    print("Testing Vision Intelligence Logic...")
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))
    
    # Mocking dependencies to test logic flow
    with patch('actions.vision_actions._get_current_frame') as mock_frame, \
         patch('actions.vision_actions._get_yolo_detector') as mock_yolo, \
         patch('actions.vision_actions._get_scene_descriptor') as mock_blip, \
         patch('actions.vision_actions.read_text') as mock_ocr:
        
        # Setup Mocks
        mock_frame.return_value = "fake_frame"
        
        # Scenario 1: Book is visible
        mock_yolo.return_value.detect.return_value = {"objects": ["person", "book"]}
        mock_blip.return_value.describe.return_value = {"description": "a person holding a book"}
        mock_ocr.return_value = {"text": "Once upon a time", "message": "I read 'Once upon a time'"}
        
        from actions.vision_actions import analyze_scene
        
        print("\nScenario 1: Book detected in scene")
        result = analyze_scene(prompt="Analyze this")
        
        print(f"Result Message: {result.get('message')}")
        assert "Once upon a time" in result.get('message')
        print("SUCCESS: Auto-OCR triggered for book.")
        
        # Scenario 2: No book, just a person
        mock_yolo.return_value.detect.return_value = {"objects": ["person"]}
        mock_blip.return_value.describe.return_value = {"description": "a person standing"}
        mock_ocr.reset_mock()
        
        print("\nScenario 2: No text-heavy objects")
        result = analyze_scene(prompt="Analyze this")
        print(f"Result Message: {result.get('message')}")
        assert not mock_ocr.called
        print("SUCCESS: Generic analysis used.")

if __name__ == "__main__":
    test_intelligence()
