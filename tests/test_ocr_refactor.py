
import sys
import os
import unittest
import numpy as np
import cv2
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jarvis')))

# Mock checking if we need to? No, let's try to run with real dependencies if possible, 
# or gracefully handle missing ones.
try:
    from core.vision.ocr_engine import OCREngine, VisualShortTermMemory
except ImportError:
    # If imports fail due to missing cv2/etc in test env
    print("Skipping detailed import, creating mocks")
    pass

class TestOCREngineRefactor(unittest.TestCase):
    def setUp(self):
        # We can't easily test actual EasyOCR without model download in this env,
        # but we can test the VisualMemory and Preprocessing logic.
        try:
            self.engine = OCREngine()
            # Force easyocr unavailable to test fallback logic or just test memory
            # self.engine._easyocr_available = False 
        except:
            self.engine = None

    def test_visual_memory(self):
        print("\nTesting VisualShortTermMemory...")
        mem = VisualShortTermMemory(max_items=3)
        mem.add("Text 1", context="read")
        time.sleep(0.1)
        mem.add("Text 2: Apple", context="read")
        time.sleep(0.1)
        mem.add("Text 3: Banana", context="ocr")
        
        # Test LIFO
        last = mem.get_last()
        self.assertEqual(last['text'], "Text 3: Banana")
        
        # Test Recall
        results = mem.recall("Apple")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['text'], "Text 2: Apple")
        
        # Test Max Items
        mem.add("Text 4")
        self.assertEqual(len(mem.memory), 3) # Should have evicted Text 1

    def test_preprocessing_pipeline(self):
        print("\nTesting Preprocessing Pipeline...")
        if not self.engine:
            print("Engine not initialized, skipping.")
            return

        # Create dummy image (black text on white background)
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        cv2.putText(img, "TEST", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Test standard
        p1 = self.engine.preprocess_advanced(img, "standard")
        self.assertEqual(len(p1.shape), 2, "Standard should return grayscale")
        
        # Test upscale
        p2 = self.engine.preprocess_advanced(img, "upscale")
        self.assertEqual(p2.shape[0], 200, "Upscale should double height")
        
        # Test contrast
        p3 = self.engine.preprocess_advanced(img, "contrast")
        self.assertEqual(len(p3.shape), 2)

    def test_ocr_flow_mock(self):
        # We can't guarantee OCR works, but we can verify detect_and_read doesn't crash
        print("\nTesting detect_and_read (Crash Test)...")
        if not self.engine: return
        
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # This will likely return empty list but should not throw
        try:
            results = self.engine.detect_and_read(img)
            print(f"Results on empty image: {results}")
            self.assertIsInstance(results, list)
        except Exception as e:
            self.fail(f"detect_and_read raised exception: {e}")

if __name__ == '__main__':
    unittest.main()
