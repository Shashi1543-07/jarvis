import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.brain import Brain
import json

def test_briefing():
    print("--- Testing Daily Briefing ---")
    brain = Brain()
    
    # 1. Add some mock memories first
    brain.memory.remember_conversation("How is the weather today?", "The weather is currently clear, Sir.")
    brain.memory.remember_conversation("What are my tasks?", "You have to finish the vision integration.")
    brain.memory.add_session("Completed Phase 2 of Jarvis Vision.")
    
    # 2. Ask for a briefing
    user_input = "Jarvis, give me a status briefing."
    print(f"\nUser: {user_input}")
    
    response_json = brain.think(user_input)
    response = json.loads(response_json)
    
    print(f"\nJarvis: {response.get('text', 'No response text found.')}")
    
    # Verify it identified as a briefing
    if response.get("type") == "briefing":
        print("\nSUCCESS: Briefing generated correctly.")
    else:
        print("\nFAILURE: Briefing not identified correctly.")

if __name__ == "__main__":
    test_briefing()
