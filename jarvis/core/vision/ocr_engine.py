import cv2
import numpy as np
import json
import logging
import os

# Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OCREngine")

class OCREngine:
    """
    Robust OCR Engine for JARVIS Vision.
    Supports text detection (CRAFT/EAST) and recognition (Tesseract/CRNN).
    """
    
    def __init__(self, preferred_method="easyocr"):
        self.preferred_method = preferred_method
        self.reader = None
        self._tesseract_available = False
        self._easyocr_available = False
        
        # Check EasyOCR
        try:
            import easyocr
            logger.info("Vision: Initializing EasyOCR (Neural System)...")
            self.reader = easyocr.Reader(['en'])
            self._easyocr_available = True
        except ImportError:
            logger.warning("EasyOCR not installed. Falling back to Tesseract.")
            
        # Check Pytesseract
        try:
            import pytesseract
            # Attempt to check if tesseract is in PATH
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            logger.info("Vision: Tesseract OCR available.")
        except (ImportError, Exception):
            logger.warning("Tesseract not available or not in PATH.")

    def preprocess(self, frame):
        """
        Apply preprocessing steps: grayscale, adaptive thresholding, noise removal.
        """
        # 1. Grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. Noise Removal (Bilateral Filter preserves edges)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # 3. Adaptive Thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh

    def detect_and_read(self, frame):
        """
        Main function to detect text regions and perform OCR.
        Returns structured JSON output.
        """
        results = []
        
        if self._easyocr_available and (self.preferred_method == "easyocr" or not self._tesseract_available):
            # EasyOCR performs detection (CRAFT) and recognition (CRNN) in one go
            # and returns [([[x,y],[x,y],[x,y],[x,y]], text, confidence), ...]
            raw_results = self.reader.readtext(frame)
            for (bbox, text, prob) in raw_results:
                # Convert bbox to standard [x, y, w, h] or similar
                # EasyOCR returns 4 corners
                (tl, tr, br, bl) = bbox
                results.append({
                    "detected_text": text,
                    "bounding_box": [int(tl[0]), int(tl[1]), int(br[0] - tl[0]), int(br[1] - tl[1])],
                    "confidence": float(prob),
                    "language": "en" # Default to English for now
                })
        
        elif self._tesseract_available:
            import pytesseract
            # Use Tesseract for both detection and recognition
            # data returns boxes and text
            data = pytesseract.image_to_data(frame, output_type=pytesseract.Output.DICT)
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:
                    results.append({
                        "detected_text": text,
                        "bounding_box": [data['left'][i], data['top'][i], data['width'][i], data['height'][i]],
                        "confidence": float(data['conf'][i]) / 100.0,
                        "language": "en"
                    })
                    
        return results

    def read_text_from_frame(self, frame):
        """
        Public function mapping to the requested requirement.
        Returns JSON string.
        """
        # We process the raw frame as neural models prefer it, 
        # but we can also use preprocessed if Tesseract is used.
        if not self._easyocr_available and self._tesseract_available:
            frame = self.preprocess(frame)
            
        data = self.detect_and_read(frame)
        return json.dumps(data, indent=2)

def read_text_from_frame(frame):
    """Factory function for quick access"""
    engine = OCREngine()
    return engine.read_text_from_frame(frame)
