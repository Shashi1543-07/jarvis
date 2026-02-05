
import sys
import os

def test_single_char_ocr():
    print("Testing Single Character OCR Logic...")
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))
    
    try:
        from core.vision.ocr_engine import get_ocr_engine
        engine = get_ocr_engine()
        
        # Mock results for a single "A"
        mock_results = [
            {"detected_text": "A", "confidence": 0.9, "bounding_box": [100, 100, 50, 50], "engine": "easyocr"}
        ]
        
        print("\nChecking _has_valid_text for 'A'...")
        is_valid = engine._has_valid_text(mock_results)
        print(f"Is Valid: {is_valid}")
        
        if not is_valid:
            print("FAILURE: Single character 'A' should be valid.")
        else:
            print("SUCCESS: Single character 'A' is now valid.")

        # Test composite strings
        mock_results_2 = [
            {"detected_text": "H", "confidence": 0.8},
            {"detected_text": "i", "confidence": 0.8}
        ]
        print("\nChecking _has_valid_text for 'Hi'...")
        is_valid_2 = engine._has_valid_text(mock_results_2)
        print(f"Is Valid: {is_valid_2}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_single_char_ocr()
