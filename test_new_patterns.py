#!/usr/bin/env python3
"""
Test script to verify that the new relationship patterns work
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

from jarvis.core.enhanced_memory import EnhancedMemory
import re

def test_new_patterns():
    print("Testing New Relationship Patterns")
    print("=" * 50)

    # Create a fresh memory instance
    memory = EnhancedMemory()

    # Test the specific case that wasn't working
    test_inputs = [
        "I have a girlfriend, I love her, her name is Akansha",
        "Her name is Akansha, she is my girlfriend",
        "My girlfriend, her name is Akansha",
        "Girlfriend named Akansha",
        "My girlfriend Akansha"
    ]

    print(f"\nTesting {len(test_inputs)} new relationship patterns:\n")

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

if __name__ == "__main__":
    test_new_patterns()