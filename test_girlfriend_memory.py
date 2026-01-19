#!/usr/bin/env python3
"""
Test script to verify that girlfriend name is remembered across sessions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

from jarvis.core.enhanced_memory import EnhancedMemory
import json

def test_girlfriend_memory():
    print("Testing Girlfriend Memory Storage")
    print("=" * 50)

    # Create a fresh memory instance
    memory = EnhancedMemory()

    # Test different ways of mentioning a girlfriend
    test_inputs = [
        "My girlfriend's name is Emma Watson",
        "This is my girlfriend Lisa",
        "Sarah is my girlfriend",
        "I have a girlfriend named Jennifer"
    ]

    print(f"\nTesting {len(test_inputs)} different ways of mentioning a girlfriend:\n")

    for i, user_input in enumerate(test_inputs, 1):
        print(f"Test {i}: {user_input}")

        # Process the input to extract important information
        important_info = memory.extract_important_information(user_input)
        print(f"   Extracted info: {important_info}")

        # Process the conversation for memory storage
        memory.process_conversation_for_memory(user_input, "Understood, I'll remember that.")

        # Check if relationships were stored
        print(f"   Current relationships: {memory.relationships}")
        print("-" * 40)

    print(f"\nFinal Relationships Stored:")
    for person, details in memory.relationships.items():
        print(f"   {person}: {details}")

    print(f"\nSaving memory to file...")
    memory.save_memory()

    print(f"\nTest completed! Check jarvis/config/memory.json to verify relationships are saved.")

    # Also test retrieval
    print(f"\nTesting retrieval of relationship information:")
    if memory.relationships:
        for person, details in memory.relationships.items():
            print(f"   Remembering {person} as {details['type']}")
    else:
        print("   No relationships found in memory")

if __name__ == "__main__":
    test_girlfriend_memory()