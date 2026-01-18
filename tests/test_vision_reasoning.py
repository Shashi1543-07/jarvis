import sys
import os
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.brain import Brain

def test_vision_reasoning():
    print("--- Testing Conversational Vision Reasoning ---")
    brain = Brain()
    
    # Mock some vision results
    mock_results = [
        {
            "action": "detect_objects",
            "result": {
                "type": "object_detection",
                "objects": ["person", "laptop", "cup"],
                "message": "I can see 1 person, 1 laptop, and 1 cup."
            }
        },
        {
            "action": "describe_scene",
            "result": {
                "type": "scene_description",
                "description": "A person is sitting at a desk and typing on a silver laptop."
            }
        }
    ]
    
    user_input = "Jarvis, what are you seeing right now?"
    print(f"\nUser: {user_input}")
    
    response = brain.process_action_results(user_input, mock_results)
    print(f"Jarvis: {response}")

if __name__ == "__main__":
    test_vision_reasoning()
