#!/usr/bin/env python3
"""
Test to verify the relationship retrieval fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

from jarvis.core.local_brain import LocalBrain
from jarvis.core.enhanced_memory import EnhancedMemory

def test_relationship_retrieval():
    print("Testing Relationship Retrieval Fix")
    print("=" * 50)

    # Create memory with some relationships
    memory = EnhancedMemory()
    
    # Manually add a father relationship to test
    memory.remember_relationship("Ravishankar Mishra", "father", "User's father")
    memory.remember_relationship("Akansha", "girlfriend", "User's girlfriend")
    
    print(f"Added relationships: {memory.relationships}")
    
    # Create local brain with the memory
    local_brain = LocalBrain(memory)
    
    # Test queries
    test_queries = [
        "who is my father?",
        "what is my name",
        "who is my girlfriend?",
        "tell me about my father"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        # Simulate the classification process
        result = local_brain.process(query, "PERSONAL_QUERY")
        print(f"Response: {result}")

if __name__ == "__main__":
    test_relationship_retrieval()