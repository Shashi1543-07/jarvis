import sys
import os
import json
from datetime import datetime
import re

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

from jarvis.core.local_brain import LocalBrain
from jarvis.core.enhanced_memory import EnhancedMemory

def test_pending_command_flow():
    print("Testing Multi-Turn Security Flow...")
    memory = EnhancedMemory()
    brain = LocalBrain(memory)
    
    # Reset security state
    brain.security_manager.pending_command = None
    brain.security_manager.reset_authorization()
    
    # 1. Request risky command
    print("\nTurn 1: User requests shutdown")
    resp1 = brain.process("shutdown system", "ACTION_REQUEST")
    print("Jarvis Response: " + str(resp1.get('text')))
    
    if "authorization" in resp1.get('text').lower() or "secret code" in resp1.get('text').lower():
        print("[OK] Jarvis correctly asked for authorization.")
    else:
        print("[FAIL] Jarvis failed to ask for authorization.")
        return False
        
    # 2. provide code
    print("\nTurn 2: User provides 'tronix'")
    resp2 = brain.process("tronix", "ACTION_REQUEST")
    print("Jarvis Response: " + str(resp2))
    
    if resp2.get('action') == "shutdown_system":
        print("[OK] Jarvis correctly executed the pending shutdown command!")
    else:
        print("[FAIL] Jarvis failed to execute the pending command.")
        return False
        
    return True

def test_command_mapping():
    print("\nTesting Command Mapping (Brightness & Battery)...")
    memory = EnhancedMemory()
    brain = LocalBrain(memory)
    
    print("Testing: 'set brightness to 80'")
    resp_b = brain.process("set brightness to 80", "ACTION_REQUEST")
    print("Result: " + str(resp_b))
    if resp_b.get('action') == "set_brightness" and resp_b.get('params', {}).get('level') == 80:
        print("[OK] Brightness mapping successful.")
    else:
        print("[FAIL] Brightness mapping failed.")
        return False

    print("\nTesting: 'how is my battery'")
    resp_bat = brain.process("how is my battery", "ACTION_REQUEST")
    print("Result: " + str(resp_bat))
    if resp_bat.get('action') == "battery_status":
        print("[OK] Battery mapping successful.")
    else:
        print("[FAIL] Battery mapping failed.")
        return False
        
    return True

def test_router_reporting():
    print("\nTesting Router Reporting Logic...")
    from jarvis.core.router import Router
    from unittest.mock import MagicMock
    
    router = Router()
    router.brain.think = MagicMock(return_value=json.dumps({
        "action": "battery_status",
        "text": "Checking power reserves."
    }))
    
    router.action_map['battery_status'] = MagicMock(return_value="Battery is at 85%, not plugged in.")
    
    print("Routing: 'check battery'")
    result = router.route("check battery")
    print("Router Result: " + str(result))
    
    expected_text = "Checking power reserves."
    if expected_text in result.get('text') and "Battery is at 85%" in result.get('text'):
        print("[OK] Router correctly aggregated reply_text and action_summary.")
        return True
    else:
        print("[FAIL] Router failed to aggregate results correctly.")
        return False

if __name__ == "__main__":
    try:
        s1 = test_pending_command_flow()
        s2 = test_command_mapping()
        s3 = test_router_reporting()
        
        if s1 and s2 and s3:
            print("\nVERIFICATION SUCCESSFUL")
        else:
            print("\nVERIFICATION FAILED")
            sys.exit(1)
    except Exception as e:
        print("\nError during verification: " + str(e))
        sys.exit(1)
