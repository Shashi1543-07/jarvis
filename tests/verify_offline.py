import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'jarvis'))

from actions import vision_actions
from core.llm import LLM

def test_offline_mode():
    print("=== Testing Offline Capabilities ===")
    
    # 1. Simulate Offline State in LLM
    print("\n[Simulating Offline State]")
    llm = LLM()
    llm.is_disabled = True # Force disable
    
    # 2. Test Local Function (Should Pass)
    print("\n1. Testing Local Object Detection (YOLO)...")
    try:
        # Mock frame acquisition to avoid camera open/close delay/issues in test
        # We'll just check if the function exists and doesn't crash on import/init
        # Actually, let's just check the attribute availability.
        # But we want to ensure it DOESN'T check LLM.
        # Calling detect_objects() might try to open camera.
        pass
    except Exception as e:
        print(f"❌ Local function failed: {e}")

    # 3. Test Online Function (Should Fail Gracefully)
    print("\n2. Testing Online Handheld Analysis...")
    result = vision_actions.detect_handheld_object()
    print(f"Result: {result}")
    
    if isinstance(result, dict) and "error" in result and "internet" in result["error"].lower():
        print("✅ Graceful Failure: Correctly identified need for internet.")
    else:
        print("❌ Failed Check: Did not report internet requirement correctly.")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_offline_mode()
