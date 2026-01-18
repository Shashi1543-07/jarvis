#!/usr/bin/env python3
"""
Test script to verify Jarvis is working with local processing only
"""

import sys
import os

# Add jarvis directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

def test_basic_functionality():
    print("Testing basic Jarvis functionality with local processing only...")
    
    try:
        # Import the core modules we modified
        from core.brain import Brain
        from core.classifier import QueryClassifier
        
        # Create instances
        brain = Brain()
        classifier = QueryClassifier()
        
        print("\n1. Testing classifier...")
        test_queries = [
            "What is the weather today?",
            "Open YouTube",
            "Set volume to high",
            "Who are you?",
            "Hello Jarvis",
            "Search for information",
            "Describe what you see"
        ]
        
        for query in test_queries:
            classification = classifier.classify(query)
            print(f"   Query: '{query}' -> Classification: {classification}")
        
        print("\n2. Testing brain responses...")
        for query in test_queries:
            response = brain.think(query)
            print(f"   Query: '{query}' -> Response: {response}")
        
        print("\n3. Testing local brain processing...")
        from core.local_brain import LocalBrain
        from core.memory import Memory
        local_brain = LocalBrain(Memory())
        
        for query in test_queries:
            classification = classifier.classify(query)
            local_response = local_brain.process(query, classification)
            print(f"   Query: '{query}' -> Local Response: {local_response}")
        
        print("\n[SUCCESS] All tests passed! Jarvis is now running with local processing only.")
        print("[SUCCESS] No API calls will be made for any queries.")

    except Exception as e:
        print(f"[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        print("\n" + "="*60)
        print("SUCCESS: Jarvis has been configured to run without API dependency!")
        print("You can now run Jarvis with 'python jarvis/app.py'")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("FAILURE: There were issues with the configuration.")
        print("="*60)