import cv2
import numpy as np
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../jarvis')))

from core.vision.ocr_engine import OCREngine

def test_ocr_synthetic():
    print("Initializing OCR Engine...")
    engine = OCREngine()
    
    # Create a synthetic image with text
    print("Creating synthetic image with text...")
    img = np.zeros((400, 800, 3), dtype=np.uint8)
    img.fill(255) # White background
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, 'JARVIS VISION SYSTEM', (50, 100), font, 1.5, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(img, 'Robust OCR Module', (50, 200), font, 1.2, (50, 50, 50), 2, cv2.LINE_AA)
    cv2.putText(img, 'Confidence Test 123', (50, 300), font, 1, (100, 100, 100), 2, cv2.LINE_AA)
    
    # Add some rotation to simulate distortion
    center = (img.shape[1]//2, img.shape[0]//2)
    matrix = cv2.getRotationMatrix2D(center, 5, 1.0) # 5 degree rotation
    img = cv2.warpAffine(img, matrix, (img.shape[1], img.shape[0]), borderValue=(255, 255, 255))
    
    # Save for visual check
    os.makedirs("tests/data", exist_ok=True)
    cv2.imwrite("tests/data/synthetic_ocr_test.jpg", img)
    
    print("Running OCR detection...")
    json_output = engine.read_text_from_frame(img)
    results = json.loads(json_output)
    
    print(f"\nExtracted JSON Output:\n{json_output}")
    
    print("\nVerification Results:")
    found_jarvis = any("JARVIS" in res['detected_text'].upper() for res in results)
    found_ocr = any("OCR" in res['detected_text'].upper() for res in results)
    
    if found_jarvis:
        print("  ✓ Found 'JARVIS'")
    else:
        print("  ✗ Could not find 'JARVIS'")
        
    if found_ocr:
        print("  ✓ Found 'OCR'")
    else:
        print("  ✗ Could not find 'OCR'")
        
    if results:
        print(f"  ✓ Found {len(results)} text regions")
        print(f"  ✓ First bbox: {results[0]['bounding_box']}")
    else:
        print("  ✗ No text regions detected")

if __name__ == "__main__":
    test_ocr_synthetic()
