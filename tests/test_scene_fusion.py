
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis.core.vision.scene_description import SceneFuser

def test_scene_fusion():
    print("Testing Scene Context Fusion...")
    fuser = SceneFuser()
    
    # Test case 1: Office
    objects = ["laptop", "mouse", "keyboard", "person"]
    desc = "a person sitting at a desk with a computer"
    scene = fuser.infer_scene(objects, desc)
    print(f"Test 1 (Office): {scene} - {'PASS' if scene == 'office/workspace' else 'FAIL'}")
    
    # Test case 2: Bedroom
    objects = ["bed", "pillow", "person"]
    desc = "a cozy room with a bed"
    scene = fuser.infer_scene(objects, desc)
    print(f"Test 2 (Bedroom): {scene} - {'PASS' if scene == 'bedroom' else 'FAIL'}")
    
    # Test case 3: Kitchen
    objects = ["refrigerator", "oven", "sink"]
    desc = "a clean modern kitchen"
    scene = fuser.infer_scene(objects, desc)
    print(f"Test 3 (Kitchen): {scene} - {'PASS' if scene == 'kitchen' else 'FAIL'}")

if __name__ == "__main__":
    test_scene_fusion()
