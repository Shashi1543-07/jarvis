
import cv2
import os
import sys
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis.core.vision.face_manager import FaceManager

def test_face_quality():
    print("Testing Face Quality Evaluation...")
    fm = FaceManager()
    
    # Create a dummy sharp frame (noise)
    sharp_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    # Create a dummy blurry frame (solid color)
    blurry_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Large location
    loc_large = (100, 300, 300, 100) # top, right, bottom, left -> 200x200
    # Small location
    loc_small = (100, 150, 150, 100) # 50x50
    
    print("\n1. Testing Small Face:")
    res = fm.evaluate_face_quality(sharp_frame, loc_small)
    print(f"Result: {res['is_good']} - Reason: {res['reason']}")
    
    print("\n2. Testing Blurry Face:")
    res = fm.evaluate_face_quality(blurry_frame, loc_large)
    print(f"Result: {res['is_good']} - Reason: {res['reason']} (Sharpness: {res['sharpness']})")
    
    print("\n3. Testing 'Sharp' Random Noise (Technical sanity check):")
    res = fm.evaluate_face_quality(sharp_frame, loc_large)
    print(f"Result: {res['is_good']} - Reason: {res['reason']} (Sharpness: {res['sharpness']})")

if __name__ == "__main__":
    test_face_quality()
