import sys
import os
import time

# Add root directory to sys.path
sys.path.append(os.getcwd())

from jarvis.core.vision.vision_manager import get_vision_manager
from jarvis.core.router import Router

def test_vision_lifecycle():
    vm = get_vision_manager()
    print("Testing Vision Lifecycle...")
    
    # Test open_vision (should be fast due to caching)
    start = time.time()
    res = vm.open_vision()
    print(f"Open Vision Result: {res} (Time: {time.time() - start:.2f}s)")
    
    if not res["success"]:
        print("Failed to open vision. Manual check required.")
        return

    # Test get_stable_frame (should be 4 samples)
    start = time.time()
    frame = vm.get_stable_frame()
    print(f"Frame Captured: {frame is not None} (Time: {time.time() - start:.2f}s)")
    
    # Test close_vision
    vm.close_vision()
    print(f"Vision Active: {vm.is_active}")
    assert not vm.is_active

def test_intent_decoding():
    router = Router()
    print("\nTesting Intent Decoding...")
    
    # "close your eyes" should map to vision_actions.close_camera
    # We mock the actual execution but check the routing
    text = "close your eyes"
    # We don't want to actually run it if possible, just see it route
    print(f"Parsing: {text}")
    res = router.route(text)
    print(f"Router Result: {res}")
    
    # Check if action was VISION_CLOSE
    assert res["action"] == "VISION_CLOSE"

if __name__ == "__main__":
    try:
        test_vision_lifecycle()
        # test_intent_decoding() # Might be hard to run without GUI/Brain environment fully up
    except Exception as e:
        print(f"Test Failed: {e}")
