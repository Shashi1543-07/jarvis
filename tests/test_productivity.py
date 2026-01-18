import sys
import os
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.router import Router

def test_productivity():
    print("--- Testing Productivity & Coding Assistant ---")
    router = Router()
    
    # 1. Test Code Explanation
    current_file = os.path.abspath(__file__)
    text = f"Jarvis, explain the code in {current_file}"
    
    print(f"\nUser: {text}")
    res = router.route(text)
    print("\n--- JARVIS Code Analysis ---")
    print(res['text'])
    
    # 2. Test Project Analysis
    project_root = os.path.dirname(os.path.dirname(current_file))
    text2 = f"Jarvis, analyze the project structure at {project_root}"
    
    print(f"\nUser: {text2}")
    res2 = router.route(text2)
    print("\n--- JARVIS Project Architecture ---")
    print(res2['text'])

if __name__ == "__main__":
    test_productivity()
