import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os

class GestureEngine:
    def __init__(self):
        # Path to the model file
        model_path = os.path.join(os.getcwd(), 'models', 'mediapipe', 'gesture_recognizer.task')
        
        if not os.path.exists(model_path):
            print(f"GestureEngine Error: Model not found at {model_path}")
            self.recognizer = None
            return

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.GestureRecognizerOptions(base_options=base_options)
        self.recognizer = vision.GestureRecognizer.create_from_options(options)
        
        print("GestureEngine: Modern MediaPipe Tasks Recognizer initialized.")

    def detect_gesture(self, frame):
        """
        Detects hand gestures using modern MediaPipe Tasks.
        """
        if self.recognizer is None or frame is None:
            return {"success": False, "gesture": "None"}

        # Task API requires MediaPipe Image object
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Recognize gestures
        recognition_result = self.recognizer.recognize(mp_image)

        if recognition_result.gestures:
            # Get the top gesture
            top_gesture = recognition_result.gestures[0][0]
            gesture_name = top_gesture.category_name
            
            # Map MediaPipe names to our internal names if needed
            # Common names: Thumb_Up, Victory (Peace), Open_Palm (Stop), Pointing_Up, ILoveYou, etc.
            mapping = {
                "Thumb_Up": "THUMBS_UP",
                "Open_Palm": "STOP",
                "Victory": "PEACE",
                "Pointing_Up": "POINTING",
            }
            
            internal_name = mapping.get(gesture_name, gesture_name)
            
            # Extra details for specific gestures (e.g., Pointing for volume)
            details = {}
            if internal_name == "POINTING" and recognition_result.hand_landmarks:
                # Index finger tip is landmark 8
                index_tip = recognition_result.hand_landmarks[0][8]
                details["y"] = index_tip.y
            
            return {
                "success": True, 
                "gesture": internal_name,
                "confidence": top_gesture.score,
                "landmarks": recognition_result.hand_landmarks[0] if recognition_result.hand_landmarks else None,
                "details": details
            }

        return {"success": False, "gesture": "None"}

    def draw_landmarks(self, frame, landmarks):
        # Tasks API doesn't provide easy drawing utils in the same way as legacy, 
        # but we can still use common drawing patterns if needed.
        # For now, we'll return the frame as-is or implement manual drawing later.
        return frame
