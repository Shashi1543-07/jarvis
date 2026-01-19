#!/usr/bin/env python3
"""
Test the integration of the new security and app launching features with the full system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis'))

from jarvis.core.router import Router

def test_integration():
    print("Testing Integration with Router...")
    
    # Create a router instance
    router = Router()
    
    # Test cases
    test_cases = [
        ("open chrome", "Try to open Chrome browser"),
        ("what is my name", "Ask for user's name"),
        ("who is my father", "Ask for father's name"),
        ("shutdown system tronix", "Shutdown with secret code"),
        ("show my personal info tronix", "Request personal info with secret code"),
        ("adjust brightness to 70", "Adjust brightness"),
        ("launch notepad", "Launch notepad"),
    ]
    
    for user_input, description in test_cases:
        print(f"\n--- Test: {description} ---")
        print(f"Input: {user_input}")
        
        try:
            response = router.route(user_input)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_integration()