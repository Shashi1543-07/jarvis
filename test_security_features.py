#!/usr/bin/env python3
"""
Test script for the new security and app launching features
"""

def test_security_manager():
    print("Testing Security Manager...")
    from jarvis.core.security_manager import SecurityManager
    
    sm = SecurityManager()
    
    # Test secret code verification
    print(f"Secret code: {sm.secret_code}")
    print(f"Verifying 'tronix': {sm.verify_secret_code('Please allow with tronix')}")
    print(f"Verifying 'wrong': {sm.verify_secret_code('Please allow with wrong')}")
    
    # Test risky operation detection
    print(f"Is 'shutdown' risky? {sm.is_risky_operation('shutdown')}")
    print(f"Is 'open chrome' risky? {sm.is_risky_operation('open chrome')}")
    print(f"Is 'personal info' risky? {sm.is_risky_operation('show my personal info')}")
    
    print("\nSecurity manager tests completed.")

def test_app_launcher():
    print("\nTesting App Launcher...")
    from jarvis.core.security_manager import find_and_launch_app
    
    # Test with some common apps (these might not exist on your system)
    test_apps = ["notepad", "calculator", "chrome", "code"]
    
    for app in test_apps:
        print(f"Trying to launch '{app}'...")
        success, message = find_and_launch_app(app)
        print(f"  Result: {message}")
        if success:
            break  # Just test one that works
    
    print("\nApp launcher tests completed.")

if __name__ == "__main__":
    test_security_manager()
    test_app_launcher()