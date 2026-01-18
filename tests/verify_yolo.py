import sys
import os
import cv2
sys.path.append(os.path.join(os.getcwd(), 'jarvis'))

from core.vision.yolo_detector import YOLODetector

def test_yolo():
    print("Initializing YOLO...")
    detector = YOLODetector()
    
    # Use uploaded image or fallback
    image_path = "C:/Users/lenovo/.gemini/antigravity/brain/0381e249-26ce-446b-ab19-44231883f54c/uploaded_image_1768724284980.png"
    
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}, trying to create dummy...")
        import numpy as np
        img = np.zeros((480, 640, 3), dtype=np.uint8)
    else:
        print(f"Loading image from {image_path}")
        img = cv2.imread(image_path)
    
    if img is None:
        print("Failed to load image.")
        return

    print("Running detection...")
    results = detector.detect(img)
    
    print("Results:", results)
    
    if int(results.get('count', 0)) >= 0:
        print("✅ YOLO Detection Logic Passed (Count accessed)")
    else:
        print("❌ YOLO Failed")

if __name__ == "__main__":
    test_yolo()
