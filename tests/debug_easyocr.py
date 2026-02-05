
import sys
import os
import cv2
import numpy as np

def test_ocr():
    print("Testing OCREngine initialization...")
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))
    
    try:
        from core.vision.ocr_engine import get_ocr_engine
        engine = get_ocr_engine()
        
        print(f"EasyOCR Available: {engine._easyocr_available}")
        print(f"Tesseract Available: {engine._tesseract_available}")
        
        # Create dummy image
        img = np.ones((100, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, "TEST OCR 123", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        print("Running detect_and_read...")
        results = engine.detect_and_read(img)
        
        print(f"Results: {results}")
        if results:
            print(f"Extracted: {[r['detected_text'] for r in results]}")
        else:
            print("FAILURE: No text detected in dummy image!")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr()
