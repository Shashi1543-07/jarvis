#!/usr/bin/env python3
"""
Cleanup script to remove test data from memory after testing the enhanced memory system
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

from jarvis.core.enhanced_memory import EnhancedMemory

def cleanup_test_data():
    print("[CLEANUP] Cleaning up test data from memory...")
    print("=" * 50)

    # Load the current memory
    memory = EnhancedMemory()

    print(f"Before cleanup - Interests: {len(memory.interests)}")
    print(f"Before cleanup - Personal History: {len(memory.personal_history)}")
    print(f"Before cleanup - Contact Info: {memory.long_term.get('contact_info', {})}")
    
    # Remove test data from interests
    test_interests = ['pizza and Italian food', 'pizza and Italian food']  # Remove duplicates
    for interest in test_interests:
        if interest in memory.interests:
            memory.interests.remove(interest)
            print(f"Removed interest: {interest}")
    
    # Remove test data from contact info
    if 'contact_info' in memory.long_term:
        # Remove test email
        if 'email' in memory.long_term['contact_info'] and 'john.doe@example.com' in memory.long_term['contact_info']['email']:
            memory.long_term['contact_info']['email'].remove('john.doe@example.com')
            print("Removed test email: john.doe@example.com")
            
            # Clean up empty category if needed
            if not memory.long_term['contact_info']['email']:
                del memory.long_term['contact_info']['email']
        
        # Remove test phone
        if 'phone' in memory.long_term['contact_info'] and '555-123-4567' in memory.long_term['contact_info']['phone']:
            memory.long_term['contact_info']['phone'].remove('555-123-4567')
            print("Removed test phone: 555-123-4567")
            
            # Clean up empty category if needed
            if not memory.long_term['contact_info']['phone']:
                del memory.long_term['contact_info']['phone']
        
        # Clean up contact_info if empty
        if not memory.long_term['contact_info']:
            del memory.long_term['contact_info']
    
    # Remove test personal events (if any were added)
    original_length = len(memory.personal_history)
    memory.personal_history = [event for event in memory.personal_history 
                              if 'november 5th' not in event['description'].lower()]
    if len(memory.personal_history) < original_length:
        print(f"Removed test personal events related to flights")
    
    # Save the cleaned memory
    memory.save_memory()
    
    print(f"After cleanup - Interests: {len(memory.interests)}")
    print(f"After cleanup - Personal History: {len(memory.personal_history)}")
    print(f"After cleanup - Contact Info: {memory.long_term.get('contact_info', {})}")
    
    print("\n[SUCCESS] Test data cleanup completed!")
    print("Your original personal information has been preserved.")
    print("Only test data from the experiment has been removed.")

if __name__ == "__main__":
    cleanup_test_data()