import sys
import os
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.router import Router

def test_longterm_memory():
    print("--- Testing Enhanced Long-term Memory ---")
    router = Router()
    
    # Ensure memory is clean for test (optional, but good for consistency)
    router.memory.clear_long_term_memory()

    # 1. Test Memorization
    inputs = [
        "Jarvis, memorize that my car's plate number is ABC 789.",
        "Remember that my favorite coffee is a double espresso.",
        "Save this: the secret code for the lab is 4242."
    ]
    
    for text in inputs:
        print(f"\nUser: {text}")
        response = router.route(text)
        print(f"Jarvis: {response['text']}")

    # 2. Test Semantic Recall (Varied phrasing)
    recall_tests = [
        "What is my car's plate?",          # Natural follow-up
        "What coffee do I like?",           # Keyword shift
        "Do you remember any secret code?"  # Semantic match
    ]
    
    print("\n--- Testing Retrieval ---")
    for text in recall_tests:
        print(f"\nUser: {text}")
        response = router.route(text)
        print(f"Jarvis: {response['text']}")

if __name__ == "__main__":
    test_longterm_memory()
