"""
Quick Verification Test for Unified Intent Classification
Tests that the refactored IntentClassifier properly extracts slots
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

from core.nlu.intent_classifier import get_classifier
from core.context_manager import get_context_manager

def test_intent_classification():
    print("=" * 60)
    print("TESTING UNIFIED INTENT CLASSIFICATION")
    print("=" * 60)
    
    classifier = get_classifier()
    
    test_cases = [
        ("Open Chrome", "SYSTEM_OPEN_APP", "app_name"),
        ("Close Notepad", "SYSTEM_CLOSE_APP", "app_name"),
        ("Set volume to 50", "SYSTEM_CONTROL", "command"),
        ("Increase brightness by 20", "SYSTEM_CONTROL", "command"),
        ("Shutdown the computer", "SYSTEM_CONTROL", "command"),
        ("Search for python tutorials", "BROWSER_SEARCH", "query"),
        ("Remember my favorite color is blue", "MEMORY_WRITE", "content"),
        ("Read the screen", "SCREEN_OCR", None),
        ("What do you see", "VISION_DESCRIBE", None),
        ("Hello", "CONVERSATION", None),  # Should fall back to conversation
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected_intent, expected_slot_key in test_cases:
        result = classifier.classify(input_text)
        intent = result.get("intent", "UNKNOWN")
        slots = result.get("slots", {})
        confidence = result.get("confidence", 0.0)
        
        # Check intent match (partial match ok for flexibility)
        intent_match = expected_intent in intent or intent in expected_intent
        
        # Check slot extraction (if expected_slot_key is None, any slots are ok)
        slot_match = True
        if expected_slot_key:
            slot_match = expected_slot_key in slots and slots.get(expected_slot_key)
        
        if intent_match and slot_match:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1
            # Print detailed failure reason
            if not intent_match:
                print(f"\n  FAIL REASON: Intent mismatch: got '{intent}', expected '{expected_intent}'")
            if not slot_match:
                print(f"\n  FAIL REASON: Slot mismatch: expected key '{expected_slot_key}' in {slots}")
        
        print(f"\n{status}: '{input_text}'")
        print(f"  Intent: {intent} (expected: {expected_intent})")
        print(f"  Slots: {slots}")
        print(f"  Confidence: {confidence:.2f}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)}")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = test_intent_classification()
    sys.exit(0 if success else 1)
