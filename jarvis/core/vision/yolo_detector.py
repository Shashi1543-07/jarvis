"""
YOLO Detector - Object detection using YOLO11
Real-time object detection and tracking
"""

import cv2
from pathlib import Path

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("[YOLODetector] Warning: ultralytics not installed. Object detection disabled.")


class YOLODetector:
    """YOLO11 object detection wrapper"""
    
    def __init__(self, model_name="yolo11m.pt"):
        """
        Initialize YOLO detector
        
        Args:
            model_name: YOLO model to use (yolo11n, yolo11s, yolo11m, yolo11l, yolo11x)
            'n' = nano (fastest), 'm' = medium (balanced), 'x' = extra large (accurate)
        """
        self.model = None
        self.model_name = model_name
        self.failed_to_load = False # CIRCUIT BREAKER
        
        if not YOLO_AVAILABLE:
            print("[YOLODetector] YOLO not available")
            return
        
        # Lazy loading - load on first detection
        print(f"[YOLODetector] Initialized (model will load on first use)")
    
    def _load_model(self):
        """Lazy load YOLO model with GPU acceleration"""
        if self.model is None and YOLO_AVAILABLE and not self.failed_to_load:
            print(f"[YOLODetector] Loading {self.model_name} on CUDA...")
            try:
                # Force CUDA if available, fallback to CPU
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model = YOLO(self.model_name)
                self.model.to(device)
                print(f"[YOLODetector] Model loaded successfully on {device}")
            except Exception as e:
                print(f"[YOLODetector] Failed to load model: {e}")
                if "failed reading zip archive" in str(e).lower() or "central directory" in str(e).lower():
                    print("[YOLODetector] CRITICAL: Model file is corrupted.")
                    self.failed_to_load = True # Stop trying
                # Set a temporary cooldown or flag to avoid spam
                self.failed_to_load = True 
    
    def detect(self, frame, confidence_threshold=0.25):
        """
        Detect objects in frame
        
        Args:
            frame: OpenCV BGR frame
            confidence_threshold: Minimum confidence (0.0-1.0)
            
        Returns:
            dict with:
                - objects: list of object names
                - count: total count
                - details: list of dicts with name, confidence, bbox
        """
        if not YOLO_AVAILABLE:
            return {
                'objects': [],
                'count': 0,
                'details': [],
                'error': 'YOLO not available'
            }
        
        # Load model if not loaded
        self._load_model()
        
        if self.model is None:
            return {
                'objects': [],
                'count': 0,
                'details': [],
                'error': 'Model failed to load'
            }
        
        try:
            # Run inference
            results = self.model(frame, verbose=False, conf=confidence_threshold)
            
            objects = []
            details = []
            
            for result in results:
                for box in result.boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    
                    # Get confidence and class
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = self.model.names[cls]
                    
                    objects.append(label)
                    details.append({
                        'name': label,
                        'confidence': conf,
                        'bbox': (x1, y1, x2, y2)
                    })
            
            return {
                'objects': objects,
                'count': len(objects),
                'details': details
            }
            
        except Exception as e:
            return {
                'objects': [],
                'count': 0,
                'details': [],
                'error': str(e)
            }
    
    def detect_and_draw(self, frame, confidence_threshold=0.25):
        """
        Detect objects and draw bounding boxes on frame
        
        Args:
            frame: OpenCV BGR frame
            confidence_threshold: Minimum confidence
            
        Returns:
            tuple: (annotated_frame, detection_results)
        """
        results = self.detect(frame, confidence_threshold)
        annotated_frame = frame.copy()
        
        # Draw bounding boxes
        for detail in results.get('details', []):
            x1, y1, x2, y2 = detail['bbox']
            label = f"{detail['name']} {detail['confidence']:.2f}"
            
            # Draw rectangle
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label background
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(annotated_frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return annotated_frame, results
    
    def count_objects(self, frame, object_name=None, confidence_threshold=0.5):
        """
        Count specific objects or all objects
        
        Args:
            frame: OpenCV BGR frame
            object_name: Specific object to count (None = count all)
            confidence_threshold: Minimum confidence
            
        Returns:
            dict with count and list of objects
        """
        results = self.detect(frame, confidence_threshold)
        
        if object_name:
            # Count specific object
            count = results['objects'].count(object_name)
            return {
                'object': object_name,
                'count': count,
                'found': count > 0
            }
        else:
            # Count all objects
            from collections import Counter
            object_counts = Counter(results['objects'])
            
            return {
                'total': results['count'],
                'objects': dict(object_counts),
                'details': results['details']
            }
    
    def is_object_present(self, frame, object_name, confidence_threshold=0.5):
        """
        Check if a specific object is present
        
        Args:
            frame: OpenCV BGR frame
            object_name: Object to look for
            confidence_threshold: Minimum confidence
            
        Returns:
            dict with presence status
        """
        results = self.detect(frame, confidence_threshold)
        present = object_name in results['objects']
        
        count = results['objects'].count(object_name) if present else 0
        
        return {
            'object': object_name,
            'present': present,
            'count': count,
            'confidence': max([d['confidence'] for d in results['details'] 
                             if d['name'] == object_name], default=0.0)
        }
