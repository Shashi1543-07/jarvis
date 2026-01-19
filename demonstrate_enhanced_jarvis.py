#!/usr/bin/env python3
"""
Demonstration script for the enhanced Jarvis AI with memory and personality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

from jarvis.core.router import Router

def demonstrate_enhanced_features():
    print("🤖 Welcome to the Enhanced Jarvis AI Demo!")
    print("=" * 50)
    print("Features demonstrated:")
    print("- Short-term and long-term memory")
    print("- Emotional intelligence and mood tracking")
    print("- Personality adaptation")
    print("- Interest and preference learning")
    print("- Behavioral pattern recognition")
    print("- Context-aware conversations")
    print("=" * 50)
    
    # Create a router instance
    router = Router()
    
    # Simulate a conversation that showcases the enhanced features
    conversations = [
        ("Hello Jarvis", "Greeting that establishes context"),
        ("My name is Alex", "User introduces themselves"),
        ("I live in New York", "Sharing location info"),
        ("I love programming and AI", "Expressing interests"),
        ("I feel happy today", "Emotional state"),
        ("What do you know about me?", "Testing memory recall"),
        ("Can you remember that I like pizza?", "Explicit memory request"),
        ("How do I seem to you?", "Testing personality analysis"),
        ("Tell me about my interests", "Recalling learned interests"),
        ("Goodbye Jarvis", "Ending the conversation")
    ]
    
    print("\n💬 Starting demonstration conversation...\n")
    
    for i, (user_input, description) in enumerate(conversations, 1):
        print(f"Step {i}: {description}")
        print(f"👤 User: {user_input}")
        
        response = router.route(user_input)
        ai_response = response['text']
        print(f"🤖 Jarvis: {ai_response}")
        
        # Show memory status after a few exchanges
        if i in [3, 6, 9]:
            print(f"🧠 Memory Status: {len(router.memory.short_term)} recent conversations stored")
            print(f"😊 Current Mood: {router.memory.get_current_mood()}")
            print(f"🎯 Interests Identified: {list(router.memory.interests)[:3]}")
        
        print("-" * 30)
    
    print("\n🎉 Demonstration complete!")
    print(f"📊 Final Memory Stats: {router.memory.get_memory_stats()}")
    
    # Show some of the learned information
    print(f"\n📋 Summary of learned information:")
    print(f"   • Interests: {list(router.memory.interests)}")
    print(f"   • Current mood tendency: {router.memory.get_current_mood()}")
    print(f"   • Personality traits: {router.memory.personality_profile.get('traits', [])}")
    print(f"   • Recent conversations: {len(router.memory.short_term)} stored")
    
    print(f"\n✨ The enhanced Jarvis AI now remembers:")
    print("   • Your name and preferences")
    print("   • Your emotional state and mood patterns")
    print("   • Your interests and habits")
    print("   • Context from previous conversations")
    print("   • Your personality traits and behavioral patterns")

if __name__ == "__main__":
    demonstrate_enhanced_features()