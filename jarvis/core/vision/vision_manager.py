
import cv2
import threading
import time
import numpy as np

class VisionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(VisionManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.cap = None
        self.active_camera_index = None
        self.available_cameras = []
        self.is_active = False
        self.camera_lock = threading.Lock()
        self._initialized = True

    def scan_cameras(self, max_cameras_to_check=5):

        """
        Scans for available cameras by attempting to open indices.
        Returns a list of available camera indices.
        """
        print("VisionManager: Scanning for cameras...")
        available = []
        
        # We temporarily open cameras to check them
        # This might be slow if many indices are checked, but 0-3 is usually enough
        for i in range(max_cameras_to_check):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) # Use DSHOW on Windows for faster enumeration if possible
                if not cap.isOpened():
                    # Fallback to default backend if DSHOW fails or on other OS
                    cap = cv2.VideoCapture(i)
                
                if cap is not None and cap.isOpened():
                    # Read a frame to be sure
                    ret, _ = cap.read()
                    if ret:
                        available.append(i)
                        print(f"VisionManager: Found camera at index {i}")
                    cap.release()
            except Exception as e:
                print(f"VisionManager: Error checking camera {i}: {e}")
        
        self.available_cameras = available
        return available

    def select_best_camera(self):
        """
        Selects the best camera based on priority:
        1. External (High Index)
        2. Internal (Index 0 usually, but if multiple, 0 is often internal)
        
        Assumption: Higher index = External USB Camera (common behavior)
        """
        if not self.available_cameras:
            self.scan_cameras()
            
        if not self.available_cameras:
            return None

        # Sort descending - assuming higher index is external/better
        # This matches the user requirement: "assume the external camera is the one with the highest index"
        self.available_cameras.sort(reverse=True)
        return self.available_cameras[0]

    def open_vision(self):
        """
        Opens the best available camera.
        Returns:
            dict: {"success": bool, "message": str, "camera_type": str}
        """
        with self.camera_lock:
            if self.is_active and self.cap is not None and self.cap.isOpened():
                return {
                    "success": True, 
                    "message": "Vision is already active.", 
                    "camera_type": "current"
                }

            best_index = self.select_best_camera()
            
            if best_index is None:
                return {
                    "success": False, 
                    "message": "I don't have access to any visual sensors right now.", 
                    "camera_type": "none"
                }

            print(f"VisionManager: Opening camera index {best_index}...")
            try:
                # Prefer DSHOW on Windows for speed, else default
                self.cap = cv2.VideoCapture(best_index, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                     self.cap = cv2.VideoCapture(best_index)
                
                if self.cap.isOpened():
                    self.active_camera_index = best_index
                    self.is_active = True
                    
                    # Determine type for feedback
                    cam_type = "external vision module" if best_index > 0 else "internal camera"
                    if len(self.available_cameras) == 1 and best_index > 0:
                        cam_type = "external vision module" # Even if it's the only one, if index > 0 it's likely external
                    
                    return {
                        "success": True, 
                        "message": f"Using {cam_type}.", 
                        "camera_type": cam_type,
                        "index": best_index
                    }
                else:
                    return {
                        "success": False, 
                        "message": "Failed to initialize the camera stream.",
                        "camera_type": "error"
                    }
            except Exception as e:
                return {
                    "success": False, 
                    "message": f"Camera error: {str(e)}",
                    "camera_type": "error"
                }

    def close_vision(self):
        """Releases camera resources properly"""
        with self.camera_lock:
            print("VisionManager: Releasing camera resources...")
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.is_active = False
            self.active_camera_index = None
            cv2.destroyAllWindows()

    def get_frame(self):
        """Returns the current frame, or None if failed"""
        if not self.is_active or self.cap is None or not self.cap.isOpened():
            return None
        
        try:
            ret, frame = self.cap.read()
            if ret:
                return frame
            else:
                return None
        except Exception as e:
            print(f"VisionManager: Frame read error: {e}")
            return None

    def get_stable_frame(self, sample_count=5, delay=0.05):
        """
        Captures multiple frames and returns the sharpest one.
        Technique: Variance of Laplacian.
        """
        if not self.is_active or self.cap is None:
            return None
            
        frames = []
        with self.camera_lock:
            for _ in range(sample_count):
                frame = self.get_frame()
                if frame is not None:
                    frames.append(frame)
                time.sleep(delay)
                
        if not frames:
            return None
            
        # Calculate sharpness for each frame
        best_frame = frames[0]
        max_sharpness = 0
        
        for f in frames:
            try:
                gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
                sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                if sharpness > max_sharpness:
                    max_sharpness = sharpness
                    best_frame = f
            except Exception:
                continue
                
        print(f"VisionManager: Selected sharpest frame (Score: {max_sharpness:.2f}) from {len(frames)} samples.")
        return best_frame

    def get_status_message(self):
        if not self.is_active:
             return "Vision is currently inactive."
        
        mode = "external" if self.active_camera_index and self.active_camera_index > 0 else "internal"
        return f"Vision active using {mode} sensor (Index {self.active_camera_index})."

# Global Instance Accessor
def get_vision_manager():
    return VisionManager()
