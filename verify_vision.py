import sys
import os
import time

# Add project root and jarvis subdir to path
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), 'jarvis'))

print("="*60)
print("VERIFYING VISION MODULE")
print("="*60)

# 1. Check Dependencies
print("\n1. Checking Dependencies...")
try:
    import cv2
    print(f"  [OK] OpenCV installed (version {cv2.__version__})")
except ImportError:
    print("  [FAIL] OpenCV NOT installed")

try:
    import mediapipe
    print("  [OK] MediaPipe installed")
except ImportError:
    print("  [FAIL] MediaPipe NOT installed")

try:
    import pytesseract
    print("  [OK] PyTesseract installed")
except ImportError:
    print("  [FAIL] PyTesseract NOT installed")

try:
    import ultralytics
    print("  [OK] Ultralytics (YOLO) installed")
except ImportError:
    print("  [FAIL] Ultralytics NOT installed")

# 2. Check Module Import
print("\n2. Checking Module Import...")
try:
    from jarvis.actions import vision_actions
    print("  [OK] vision_actions imported successfully")
except Exception as e:
    print(f"  [FAIL] Could not import vision_actions: {e}")
    sys.exit(1)

# 3. Test Basic Actions
print("\n3. Testing Basic Actions...")
try:
    # Open Camera
    print("  Testing open_camera()...")
    res = vision_actions.open_camera(0)
    print(f"  Result: {res}")
    
    time.sleep(2)
    
    # Capture Photo
    print("  Testing capture_photo()...")
    res = vision_actions.capture_photo("test_vision_capture.jpg")
    print(f"  Result: {res}")
    
    # Close Camera
    print("  Testing close_camera()...")
    res = vision_actions.close_camera()
    print(f"  Result: {res}")
    
except Exception as e:
    print(f"  [FAIL] Action test failed: {e}")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("="*60)
