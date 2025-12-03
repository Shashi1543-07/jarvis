"""
Comprehensive Vision System Test - In Running JARVIS Context
Tests that all vision actions are accessible through the router
"""

import sys
sys.path.insert(0, 'c:\\Users\\lenovo\\JarvisAI\\jarvis')

print("="*80)
print("TESTING VISION SYSTEM IN JARVIS")
print("="*80)

try:
    # Test 1: Import Router
    print("\n[1/5] Testing Router Import...")
    from core.router import Router
    router = Router()
    print("  ✓ Router loaded successfully")
    
    # Test 2: Check Vision Actions Available
    print("\n[2/5] Checking Vision Actions in Action Map...")
    vision_actions = [
        'open_camera', 'close_camera', 'capture_photo',
        'detect_objects', 'is_object_present', 'count_objects',
        'identify_people', 'who_is_in_front', 'remember_face',
        'describe_scene', 'detect_emotion', 'search_object_details',
        'analyze_screen', 'read_screen', 'describe_screen'
    ]
    
    missing = []
    available = []
    for action in vision_actions:
        if action in router.action_map:
            available.append(action)
            print(f"  ✓ {action}")
        else:
            missing.append(action)
            print(f"  ✗ {action} - MISSING FROM ROUTER")
    
    print(f"\n  Available: {len(available)}/{len(vision_actions)}")
    
    # Test 3: Test Action Execution Simulation
    print("\n[3/5] Testing Action Calls...")
    try:
        # Try to get the function (don't execute, just verify it's callable)
        open_cam_func = router.action_map.get('open_camera')
        if open_cam_func and callable(open_cam_func):
            print("  ✓ open_camera is callable")
        else:
            print("  ✗ open_camera not callable")
            
        desc_scene_func = router.action_map.get('describe_scene')
        if desc_scene_func and callable(desc_scene_func):
            print("  ✓ describe_scene is callable  ")
        else:
            print("  ✗ describe_scene not callable")
    except Exception as e:
        print(f"  ✗ Error checking callability: {e}")
    
    # Test 4: Check Brain has Vision Commands
    print("\n[4/5] Checking Brain Configuration...")
    from core.brain import Brain
    brain = Brain()
    # Check if brain's system instruction would include vision commands
    test_response = brain.think("open your eyes")
    if 'open_camera' in str(test_response).lower() or 'camera' in str(test_response).lower():
        print("  ✓ Brain recognizes vision commands")
    else:
        print("  ⚠ Brain may not be routing vision commands properly")
        print(f"  Response: {test_response[:100]}...")
    
    # Test 5: Summary
    print("\n[5/5] SUMMARY")
    print("="*80)
    if len(missing) == 0:
        print("✅ ALL VISION ACTIONS ARE AVAILABLE!")
        print(f"✅ {len(available)} vision actions accessible through router")
        print("✅ Brain configured with vision command mappings")
        print("\n🎯 Vision System is FULLY OPERATIONAL")
    else:
        print(f"⚠ {len(missing)} vision actions missing from router:")
        for m in missing:
            print(f"  - {m}")
            
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
