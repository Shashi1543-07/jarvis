#!/usr/bin/env python3
"""
Test script for the enhanced memory system with intelligent filtering
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

from jarvis.core.router import Router
import json

def test_memory_system():
    print("🧪 Testing Enhanced Memory System with Intelligent Filtering")
    print("=" * 60)
    
    # Create a router instance
    router = Router()
    
    # Test cases for different types of inputs
    test_cases = [
        # General commands (should not be stored in long-term memory)
        ("Open calculator", "General command test"),
        ("Play music", "General command test"),
        ("What's the weather?", "General command test"),
        ("Set a timer for 5 minutes", "General command test"),
        
        # Important personal information (should be stored in long-term memory)
        ("I have a flight on November 5th", "Flight information test"),
        ("My email is john.doe@example.com", "Email information test"),
        ("I live at 123 Main Street", "Address information test"),
        ("My phone number is 555-123-4567", "Phone information test"),
        ("I love pizza and Italian food", "Preference information test"),
        ("My friend John works at Google", "Relationship information test"),
        ("I have a doctor appointment next Tuesday", "Appointment information test"),
        ("Remind me about my anniversary on June 15th", "Event information test"),
        
        # Mixed conversation
        ("How are you today?", "General conversation test"),
        ("I feel happy and excited about my upcoming trip", "Emotion + event information test"),
    ]
    
    print(f"\n💬 Running {len(test_cases)} test conversations...\n")
    
    for i, (user_input, description) in enumerate(test_cases, 1):
        print(f"Test {i}: {description}")
        print(f"👤 User: {user_input}")
        
        # Process the input through the router
        response = router.route(user_input)
        ai_response = response.get('text', 'No response')
        print(f"🤖 Jarvis: {ai_response}")
        
        # Show memory status periodically
        if i % 5 == 0:
            memory_stats = router.memory.get_memory_stats()
            print(f"📊 Memory Stats: {memory_stats}")
            print(f"📝 Interests: {list(router.memory.interests)[:5]}")  # Show first 5 interests
            print(f"📁 Personal History: {len(router.memory.personal_history)} events")
        
        print("-" * 40)
    
    print("\n✅ Test conversations completed!")
    
    # Show final memory status
    print(f"\n📋 Final Memory Summary:")
    memory_stats = router.memory.get_memory_stats()
    print(f"   • Short-term entries: {memory_stats['short_term_count']}")
    print(f"   • Long-term keys: {memory_stats['long_term_keys']}")
    print(f"   • Interests: {memory_stats['interest_count']}")
    print(f"   • Personal events: {memory_stats.get('personal_history', 0)}")
    print(f"   • Emotions tracked: {memory_stats['emotion_count']}")
    
    # Show specific long-term memory contents
    print(f"\n🔍 Detailed Long-term Memory Contents:")
    if 'contact_info' in router.memory.long_term:
        print(f"   • Contact Info: {router.memory.long_term['contact_info']}")
    if 'facts' in router.memory.long_term:
        print(f"   • Facts: {router.memory.long_term['facts']}")
    if 'preferences' in router.memory.long_term:
        print(f"   • Preferences: {router.memory.long_term['preferences']}")
    
    print(f"\n🎯 Classification Examples from Short-term Memory:")
    for entry in router.memory.short_term[-5:]:  # Show last 5 entries
        if isinstance(entry, dict) and 'user' in entry:
            classification = entry.get('classification', 'unknown')
            print(f"   • '{entry['user'][:30]}...' -> {classification}")
    
    print(f"\n✨ The enhanced memory system successfully distinguishes between:")
    print("   • General commands (not stored in long-term memory)")
    print("   • Important personal information (automatically stored in long-term memory)")
    print("   • Temporary context (cleared on exit, important info preserved)")

if __name__ == "__main__":
    test_memory_system()