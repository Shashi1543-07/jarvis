#!/usr/bin/env python3
"""
Test to verify the relationship processing logic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

from jarvis.core.enhanced_memory import EnhancedMemory

def test_relationship_processing():
    print("Testing Relationship Processing Logic")
    print("=" * 50)

    # Create a fresh memory instance
    memory = EnhancedMemory()

    # Test the specific case
    test_input = "my father's name is ravishankar mishra"
    
    print(f"Input: {test_input}")
    
    # Extract important information
    important_info = memory.extract_important_information(test_input)
    print(f"Extracted info: {important_info}")
    
    # Process for memory storage
    memory.process_conversation_for_memory(test_input, "Understood")
    
    print(f"Relationships after processing: {memory.relationships}")
    
    # Test another case
    test_input2 = "my girlfriend's name is akansha"
    print(f"\nInput 2: {test_input2}")
    
    important_info2 = memory.extract_important_information(test_input2)
    print(f"Extracted info 2: {important_info2}")
    
    memory.process_conversation_for_memory(test_input2, "Understood")
    
    print(f"Relationships after processing 2: {memory.relationships}")
    
    # Save to verify it persists
    memory.save_memory()
    print("Memory saved to file.")

if __name__ == "__main__":
    test_relationship_processing()