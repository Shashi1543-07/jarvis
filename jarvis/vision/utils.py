import cv2
import time
import threading

class CameraManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CameraManager, cls).__new__(cls)
                cls._instance.cap = None
                cls._instance.is_active = False
        return cls._instance
    
    def open_camera(self, camera_id=0):
        if self.cap is not None and self.cap.isOpened():
            return True
            
        self.cap = cv2.VideoCapture(camera_id)
        if self.cap.isOpened():
            self.is_active = True
            return True
        return False
    
    def close_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_active = False
        cv2.destroyAllWindows()
        
    def get_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

def get_camera():
    return CameraManager()
