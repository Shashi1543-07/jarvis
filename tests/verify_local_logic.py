import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'jarvis'))

from core.local_brain import LocalBrain
from core.classifier import QueryClassifier
from core.memory import Memory

def test_logic():
    print("Initializing Core Modules...")
    brain = LocalBrain(Memory())
    classifier = QueryClassifier()
    
    test_cases = [
        # Vision Actions
        ("what do you see", "ACTION_REQUEST", "describe_scene"),
        ("read this text", "ACTION_REQUEST", "read_text"),
        ("analyse the scene", "ACTION_REQUEST", "describe_scene"),
        ("recognise me", "ACTION_REQUEST", "identify_people"),
        ("detect objects", "ACTION_REQUEST", "detect_objects"),
        
        # Identity (Local)
        ("who am i", "PERSONAL_QUERY", None), 
        ("who i am", "PERSONAL_QUERY", None),
        
        # Web (Should NOT be Personal)
        ("who is einstein", "WEB_ONLY_QUERY", None),
        ("tell me about space", "WEB_ONLY_QUERY", None),
        
        # System
        ("what time is it", "SYSTEM_COMMAND", "check_time"),
    ]
    
    failed = False
    for text, expected_class, expected_action in test_cases:
        print(f"\nTesting Input: '{text}'")
        
        # 1. Test Classification
        cls = classifier.classify(text)
        print(f"  Classified as: {cls}")
        
        if cls != expected_class:
            print(f"  ❌ Classification FAIL: Expected {expected_class}, got {cls}")
            failed = True
            continue
            
        # 2. Test Processing (Only if not WEB_ONLY)
        if cls == "WEB_ONLY_QUERY":
            print("  ✅ Classification PASS (Skipping Local Processing)")
            continue
            
        response = brain.process(text, cls)
        print(f"  Response: {response}")
        
        if expected_action:
            if response.get("action") == expected_action:
                print("  ✅ Action PASS")
            else:
                print(f"  ❌ Action FAIL: Expected {expected_action}")
                failed = True
        else:
            # Check text
            if response.get("text") and "offline" not in response.get("text").lower():
                print("  ✅ Text PASS")
            else:
                print("  ❌ Text FAIL: Got offline fallback or empty")
                failed = True
            
    if failed:
        sys.exit(1)
    else:
        print("\nAll logic tests passed!")

if __name__ == "__main__":
    test_logic()
