import sys
import os
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.brain import Brain

def test_ocr_reasoning():
    print("--- Testing Conversational OCR Reasoning ---")
    brain = Brain()
    
    # Mock OCR result
    mock_results = [
        {
            "action": "read_text",
            "result": {
                "type": "ocr_result",
                "text": "WARNING: High Voltage. Authorized Personnel Only.",
                "message": "Extracted text: WARNING: High Voltage. Authorized Personnel Only."
            }
        }
    ]
    
    user_input = "Jarvis, what does that sign say?"
    print(f"\nUser: {user_input}")
    
    response = brain.process_action_results(user_input, mock_results)
    print(f"Jarvis: {response}")

if __name__ == "__main__":
    test_ocr_reasoning()
