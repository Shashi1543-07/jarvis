import cv2
import os
import numpy as np
import json
import logging
import time
import datetime
import traceback
import sys
from collections import deque

# Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OCREngine")

class VisualShortTermMemory:
    """
    Stores recent vision/OCR results for recall.
    """
    def __init__(self, max_items=20):
        self.memory = deque(maxlen=max_items)
    
    def add(self, text, details=None, context="ocr"):
        entry = {
            "timestamp": time.time(),
            "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": text,
            "details": details or [],
            "context": context
        }
        self.memory.appendleft(entry)
        
    def recall(self, query=None, limit=5):
        """
        Recall recent items. If query is provided, simple keyword filter.
        """
        results = []
        for item in self.memory:
            if not query or query.lower() in item['text'].lower() or query.lower() in item['context']:
                results.append(item)
            if len(results) >= limit:
                break
        return results

    def get_last(self):
        return self.memory[0] if self.memory else None

class OCREngine:
    """
    Robust OCR Engine for JARVIS Vision.
    Supports text detection (CRAFT/EAST) and recognition (Tesseract/CRNN).
    Includes advanced specific preprocessing pipeline and memory.
    """
    def __init__(self, preferred_method="easyocr"):
        self.preferred_method = preferred_method
        self.reader = None
        self._tesseract_available = False
        self._easyocr_available = False
        
        # Init Memory
        self.memory = VisualShortTermMemory()
        
        # Check EasyOCR (PRIORITY)
        try:
            print("Vision: Attempting to import easyocr...")
            import easyocr
            print("Vision: Initializing EasyOCR Reader (Neural System)...")
            try:
                # Attempt GPU first
                self.reader = easyocr.Reader(['en'], gpu=True, verbose=False) 
                print("OCREngine: EasyOCR initialized successfully on GPU/CUDA.")
            except Exception as gpu_err:
                print(f"OCREngine: GPU Init failed ({gpu_err}), falling back to CPU...")
                self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                print("OCREngine: EasyOCR initialized successfully on CPU.")
            
            self._easyocr_available = True
            logger.info("OCREngine: EasyOCR initialized successfully.")
        except ImportError as ie:
            print(f"EasyOCR ImportError: {ie}")
            logger.warning(f"EasyOCR ImportError: {ie}")
            logger.info(f"Python sys.path: {sys.path}")
            logger.warning("EasyOCR not installed or dependency missing.")
        except Exception as e:
             print(f"EasyOCR Init Failed: {e}")
             logger.error(f"EasyOCR Init Failed: {e}. Falling back.")
             traceback.print_exc()
            
        # Check Pytesseract (FALLBACK)
        try:
            import pytesseract
            # On Windows, it often requires manual path config if not in ENV
            try:
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
                logger.info("Vision: Tesseract OCR available.")
            except:
                # Common windows path
                tessa_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                if os.path.exists(tessa_path):
                    pytesseract.pytesseract.tesseract_cmd = tessa_path
                    self._tesseract_available = True
                    logger.info("Vision: Tesseract OCR found at default Windows path.")
                else:
                    logger.warning("Tesseract binary not found.")
        except (ImportError, Exception):
            logger.warning("Tesseract module error.")

        if not self._easyocr_available and not self._tesseract_available:
            logger.critical("CRITICAL: No OCR engine available!")

    def preprocess_advanced(self, frame, method="standard"):
        """
        Apply separate pipelines for preprocessing.
        """
        try:
            if method == "standard":
                # Just Grayscale
                if len(frame.shape) == 3:
                    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                return frame
                
            elif method == "contrast":
                # Grayscale + CLAHE (Contrast Limited Adaptive Histogram Equalization)
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                return clahe.apply(gray)
                
            elif method == "upscale":
                # Resize 2x for small text
                return cv2.resize(frame, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
                
            elif method == "binary":
                # Adaptive Thresholding
                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    gray = frame
                return cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
        except Exception as e:
            logger.error(f"Preprocessing error ({method}): {e}")
            return frame
            
        return frame

    def _isolate_text_regions(self, frame):
        """
        Uses standard OpenCV morphology to find text-like blobs (document pages).
        Returns a list of cropped images containing potential text.
        """
        try:
            # 1. Grayscale & Blur
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            blur = cv2.GaussianBlur(gray, (7, 7), 0)
            
            # 2. Threshold
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY_INV, 11, 2)
            
            # 3. Dilate to connect text characters into lines/blocks
            # Pass A: Traditional lines (Wide kernel)
            kernel_wide = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
            dilate_wide = cv2.dilate(thresh, kernel_wide, iterations=1)
            
            # Pass B: Large single characters (Square kernel)
            kernel_sq = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
            dilate_sq = cv2.dilate(thresh, kernel_sq, iterations=1)
            
            # Combine
            dilate = cv2.bitwise_or(dilate_wide, dilate_sq)
            
            # 4. Find Contours
            contours, _ = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 5. Filter Candidates
            crops = []
            frame_area = frame.shape[0] * frame.shape[1]
            
            for c in contours:
                x, y, w, h = cv2.boundingRect(c)
                area = w * h
                aspect = w / float(h)
                
                # Filter noise: Must be at least 1% of screen, and vaguely rectangular
                if area > (frame_area * 0.01) and area < (frame_area * 0.9):
                    rect = (x, y, w, h)
                    # Expand crop slightly
                    pad = 10
                    x = max(0, x - pad); y = max(0, y - pad)
                    w = min(frame.shape[1] - x, w + 2*pad)
                    h = min(frame.shape[0] - y, h + 2*pad)
                    
                    crop = frame[y:y+h, x:x+w]
                    crops.append(crop)
            
            # Sort by area (largest text block first)
            crops.sort(key=lambda x: x.shape[0] * x.shape[1], reverse=True)
            return crops[:3] # Return top 3 regions
            
        except Exception as e:
            logger.error(f"Region Isolation Failed: {e}")
            return []

    def detect_and_read(self, frame, prioritize_method="standard", timeout=10.0):
        """
        Main function to detect text regions and perform OCR.
        Optimized: Quick check -> Regional isolation -> Regional enhancement.
        """
        start_time = time.time()
        if frame is None:
            return []

        all_results = []
        
        # Pipeline 1: Raw/Standard (Fastest)
        print("OCR: Attempting Pass 1 (Standard Core)...")
        results = self._process_frame(frame)
        
        if self._has_valid_text(results):
            final_text = " ".join([r['detected_text'] for r in results if r.get('confidence', 0) > 0.3])
            if final_text.strip():
                self.memory.add(final_text, results)
            logger.info(f"OCR: Fast exit (Pass 1).")
            return results

        # CHECK TIMEOUT
        if time.time() - start_time > timeout:
            return []

        # Pipeline 2: Document Mode (Region Isolation)
        print("OCR: Attempting Pass 2 (Region Isolation)...")
        regions = self._isolate_text_regions(frame)
        
        if regions:
            for i, crop in enumerate(regions[:2]):
                if time.time() - start_time > timeout: break
                
                print(f"OCR: Scanning Region {i+1} (Enhanced)...")
                enhanced = self.preprocess_advanced(crop, "contrast")
                r_res = self._process_frame(enhanced)
                
                if not self._has_valid_text(r_res):
                    print(f"OCR: Scanning Region {i+1} (Upscaled)...")
                    upscaled = self.preprocess_advanced(crop, "upscale")
                    r_res = self._process_frame(upscaled)
                
                all_results.extend(r_res)

        # Pipeline 3: Global Adaptive Binary (Great for black text on white paper)
        if not self._has_valid_text(all_results) and time.time() - start_time < timeout:
            print("OCR: Attempting Pass 3 (Global Binary)...")
            binary = self.preprocess_advanced(frame, "binary")
            all_results.extend(self._process_frame(binary))

        # Pipeline 4: Full-Center Upscale (Focus on where user likely holds paper)
        if not self._has_valid_text(all_results) and time.time() - start_time < timeout:
            print("OCR: Attempting Pass 4 (Center Zoom 2.5x)...")
            h, w = frame.shape[:2]
            # Focus on center 70%
            ch1, ch2 = int(h*0.15), int(h*0.85)
            cw1, cw2 = int(w*0.15), int(w*0.85)
            center_crop = frame[ch1:ch2, cw1:cw2]
            
            zoom = cv2.resize(center_crop, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
            all_results.extend(self._process_frame(zoom))
        
        # Final Verification (Lowered to 0.25)
        valid_final = [r for r in all_results if r.get('confidence', 0) > 0.2]
        if self._has_valid_text(valid_final):
            final_text = " ".join([r['detected_text'] for r in valid_final])
            self.memory.add(final_text, valid_final)
            logger.info("OCR: Successful detection in High-Sensitivity fallback.")
            return valid_final
            
        return all_results

    def _process_frame(self, frame):
        """Internal helper to run the engine on a specific image frame"""
        results = []
        
        try:
            if self._easyocr_available:
                # EasyOCR sometimes misses on first hit if model is still loading or thread contention
                for _ in range(2):
                    raw_results = self.reader.readtext(frame)
                    if raw_results: break
                    time.sleep(0.1)

                for (bbox, text, prob) in raw_results:
                    (tl, tr, br, bl) = bbox
                    results.append({
                        "detected_text": text,
                        "bounding_box": [int(tl[0]), int(tl[1]), int(br[0] - tl[0]), int(br[1] - tl[1])],
                        "confidence": float(prob),
                        "engine": "easyocr"
                    })
            
            elif self._tesseract_available:
                import pytesseract
                # Convert to RGB if standard generic frame, Tesseract expects RGB/Gray
                # If frame is grayscale (2D), skip conversion
                if len(frame.shape) == 3:
                     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                     rgb = frame
                     
                data = pytesseract.image_to_data(rgb, output_type=pytesseract.Output.DICT)
                for i in range(len(data['text'])):
                    text = data['text'][i].strip()
                    if text:
                        results.append({
                            "detected_text": text,
                            "bounding_box": [data['left'][i], data['top'][i], data['width'][i], data['height'][i]],
                            "confidence": float(data['conf'][i]) / 100.0,
                            "engine": "tesseract"
                        })
        except Exception as e:
            logger.error(f"OCR Scan Error: {e}")
            
        return results

    def _has_valid_text(self, results):
        """Heuristic to check if results look like readable text, not noise"""
        if not results: return False
        
        # Join text and check length/alphanum
        combined = "".join([r['detected_text'] for r in results]).strip()
        if len(combined) < 1: return False
        
        # Check average confidence
        total_conf = sum([r.get('confidence', 0) for r in results])
        avg_conf = total_conf / len(results) if results else 0
        return avg_conf > 0.25

    def recall_recent(self, query=None):
        return self.memory.recall(query)

    def read_text_from_frame(self, frame):
        data = self.detect_and_read(frame)
        return json.dumps(data, indent=2)

# Singleton factory
_ocr_engine_instance = None
def get_ocr_engine():
    global _ocr_engine_instance
    if _ocr_engine_instance is None:
        _ocr_engine_instance = OCREngine()
    return _ocr_engine_instance

