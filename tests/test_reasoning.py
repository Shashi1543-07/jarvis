import sys
import os
import json

# Add the project root to path to import core modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.brain import Brain

def test_local_reasoning():
    print("--- Testing Jarvis Local Reasoning ---")
    brain = Brain()
    
    queries = [
        "Hello Jarvis, identify yourself.",
        "How do steam engines work?",
        "What is the date today?"
    ]
    
    for q in queries:
        print(f"\nUser: {q}")
        response_json = brain.think(q)
        response = json.loads(response_json)
        print(f"Jarvis: {response.get('text')}")

if __name__ == "__main__":
    test_local_reasoning()
