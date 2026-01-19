import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))
from core.memory import Memory

def test_persistence():
    print("Testing Short-Term Memory Persistence...")
    
    # 1. Initialize memory and add context
    m1 = Memory()
    m1.short_term = [] # Clear for test
    m1.remember_conversation("Hello Jarvis", "Greetings Sir")
    m1.save_memory()
    print(f"Added turn: {m1.short_term}")
    
    # 2. Reload memory
    m2 = Memory()
    print(f"Reloaded turns: {m2.short_term}")
    
    if len(m2.short_term) > 0 and m2.short_term[0]['user'] == "Hello Jarvis":
        print("SUCCESS: Short-term memory persisted!")
    else:
        print("FAILURE: Short-term memory did not persist.")

if __name__ == "__main__":
    test_persistence()
