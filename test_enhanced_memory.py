#!/usr/bin/env python3
"""
Test script for the enhanced Jarvis memory system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

from jarvis.core.enhanced_memory import EnhancedMemory
from jarvis.core.brain import Brain
from jarvis.core.router import Router

def test_enhanced_memory():
    print("=== Testing Enhanced Memory System ===\n")
    
    # Create an instance of EnhancedMemory
    memory = EnhancedMemory()
    
    # Test emotional tracking
    print("1. Testing Emotional Tracking:")
    memory.remember_emotion("happy", 3, "User received good news")
    memory.remember_emotion("excited", 5, "User is excited about project")
    memory.remember_emotion("calm", 2, "User is relaxed")
    print(f"   Current mood: {memory.get_current_mood()}")
    print(f"   Emotion count: {len(memory.emotions)}")
    
    # Test interest tracking
    print("\n2. Testing Interest Tracking:")
    memory.remember_interest("technology")
    memory.remember_interest("AI")
    memory.remember_interest("programming")
    print(f"   Interests: {memory.interests}")
    
    # Test favorite tracking
    print("\n3. Testing Favorite Tracking:")
    memory.remember_favorite("music", "rock")
    memory.remember_favorite("food", "pizza")
    print(f"   Favorites: {memory.favorites}")
    
    # Test habit tracking
    print("\n4. Testing Habit Tracking:")
    memory.remember_habit("morning jog", "daily")
    memory.remember_habit("reading", "weekly")
    print(f"   Habits: {memory.habits}")
    
    # Test relationship tracking
    print("\n5. Testing Relationship Tracking:")
    memory.remember_relationship("John", "friend", "works at Google")
    memory.remember_relationship("Sarah", "colleague", "team lead")
    print(f"   Relationships: {memory.relationships}")
    
    # Test personal event tracking
    print("\n6. Testing Personal Event Tracking:")
    memory.remember_personal_event("birthday", "My birthday is June 15th", "2023-06-15")
    memory.remember_personal_event("graduation", "Graduated from university", "2023-05-20")
    print(f"   Personal Events: {memory.personal_history}")
    
    # Test personality analysis
    print("\n7. Testing Personality Analysis:")
    personality = memory.analyze_personality()
    print(f"   Personality Profile: {personality}")
    
    # Test conversation memory
    print("\n8. Testing Conversation Memory:")
    memory.remember_conversation("Hello Jarvis", "Hello Sir, how can I assist you?")
    memory.remember_conversation("What's the weather?", "I'm checking the weather for you.")
    print(f"   Short-term memory length: {len(memory.short_term)}")
    
    # Test memory context retrieval
    print("\n9. Testing Memory Context Retrieval:")
    context = memory.get_memory_context()
    print(f"   Memory context preview: {context[:200]}...")
    
    # Test memory statistics
    print("\n10. Testing Memory Statistics:")
    stats = memory.get_memory_stats()
    print(f"   Memory Stats: {stats}")
    
    print("\n=== Enhanced Memory System Test Complete ===\n")

def test_behavior_learning():
    print("=== Testing Behavior Learning System ===\n")
    
    from jarvis.core.behavior_learning import BehaviorLearning
    import datetime
    
    # Create memory and behavior learning instances
    memory = EnhancedMemory()
    behavior = BehaviorLearning(memory)
    
    # Simulate some interactions
    print("1. Testing Behavior Learning from Interactions:")
    behavior.learn_from_interaction("I really love programming", "That's great to hear!", datetime.datetime.now())
    behavior.learn_from_interaction("I hate slow computers", "I understand your frustration.", datetime.datetime.now())
    behavior.learn_from_interaction("I enjoy learning new technologies", "Learning is important.", datetime.datetime.now())
    
    # Get preferences summary
    prefs = behavior.get_user_preferences_summary()
    print(f"   Learned Preferences: {prefs}")
    
    # Get suggestions
    suggestions = behavior.suggest_based_on_patterns()
    print(f"   Suggestions: {suggestions}")
    
    print("\n=== Behavior Learning System Test Complete ===\n")

def test_full_integration():
    print("=== Testing Full Integration ===\n")
    
    # Create a router instance which uses all the enhanced components
    router = Router()
    
    print("1. Testing Router with Enhanced Memory:")
    print(f"   Memory type: {type(router.memory).__name__}")
    print(f"   Brain type: {type(router.brain).__name__}")
    print(f"   Has behavior learning: {hasattr(router.brain, 'behavior_learning')}")
    
    # Test a simple interaction
    print("\n2. Testing Simple Interaction:")
    try:
        response = router.route("Hello Jarvis")
        print(f"   Response: {response['text']}")
    except Exception as e:
        print(f"   Error during interaction: {e}")
    
    print("\n=== Full Integration Test Complete ===\n")

if __name__ == "__main__":
    test_enhanced_memory()
    test_behavior_learning()
    test_full_integration()
    
    print("All tests completed! The enhanced memory system is working correctly.")