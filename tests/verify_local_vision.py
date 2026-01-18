import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'jarvis'))

from core.local_brain import LocalBrain
from core.memory import Memory

def test_vision_logic():
    print("Initializing LocalBrain...")
    brain = LocalBrain(Memory())
    
    test_cases = [
        ("what do you see", "describe_scene"),
        ("read this text", "read_text"),
        ("is there text here", "read_text"),
        ("what am i holding", "detect_handheld_object"),
        ("who is in front of me", "identify_people"),
        ("scan this area", "detect_objects"),
        ("open your eyes", "open_camera") # Should still work
    ]
    
    failed = False
    for text, expected_action in test_cases:
        print(f"\nTesting Input: '{text}'")
        # Simulate classification (LocalBrain usually relies on Brain to classify, 
        # but here we are calling process directly. 
        # Wait, LocalBrain.process takes (text, classification).
        # We need to simulate the classifier's output for these inputs.)
        
        # Simple heuristic for classification similar to what Classifier would do
        # or just pass ACTION_REQUEST as that's what triggers these checks.
        classification = "ACTION_REQUEST"
        
        response = brain.process(text, classification)
        print(f"Response: {response}")
        
        if response.get("action") == expected_action:
            print("✅ PASS")
        else:
            print(f"❌ FAIL: Expected action '{expected_action}', got '{response.get('action')}'")
            failed = True
            
    if failed:
        sys.exit(1)
    else:
        print("\nAll logical tests passed!")

if __name__ == "__main__":
    test_vision_logic()
