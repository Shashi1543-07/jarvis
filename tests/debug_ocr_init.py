
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OCR_DEBUG")

def test_init():
    print(f"Python path: {sys.path}")
    try:
        import easyocr
        print("Import easyocr SUCCESS")
        print(f"EasyOCR file: {easyocr.__file__}")
        
        print("Attempting to create easyocr.Reader...")
        reader = easyocr.Reader(['en'], gpu=True, verbose=True)
        print("Reader creation SUCCESS")
        
    except ImportError as ie:
        print(f"ImportError detected: {ie}")
    except Exception as e:
        print(f"General Exception in initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_init()
