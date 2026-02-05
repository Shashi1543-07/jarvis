import cv2
import time
import threading
from core.vision.vision_manager import get_vision_manager

class CameraManager:
    """
    Legacy wrapper around the new core VisionManager.
    Ensures backward compatibility while providing intelligent camera selection.
    """
    def __init__(self):
        self.vm = get_vision_manager()

    def open_camera(self, camera_id=0):
        """
        Delegates to VisionManager.open_vision().
        We ignore the specific camera_id=0 default to allow intelligent selection.
        If a specific ID > 0 is passed, we might want to respect it, but for now
        Core requirements say 'automatically prefer', so we trust VisionManager.
        """
        # If the user specifically asks for a non-zero camera, we could force it, 
        # but VisionManager logic is "High Index = Priority".
        # Let's trust VisionManager's smart selection.
        result = self.vm.open_vision()
        return result["success"]
    
    def close_camera(self):
        self.vm.close_vision()
        
    def get_frame(self):
        return self.vm.get_frame()

    @property
    def is_active(self):
        return self.vm.is_active

def get_camera():
    return CameraManager()
