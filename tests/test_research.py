import sys
import os
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.router import Router

def test_deep_research():
    print("--- Testing Deep Research Agent ---")
    router = Router()
    
    # Complex topic requiring multi-source synthesis
    text = "Jarvis, perform a deep dive on the current status of the Artemis moon missions."
    
    print(f"\nUser: {text}")
    print("Wait for Jarvis to search and read multiple sources...")
    
    res = router.route(text)
    
    print("\n--- JARVIS Research Report ---")
    print(res['text'])
    print("\n------------------------------")

if __name__ == "__main__":
    test_deep_research()
