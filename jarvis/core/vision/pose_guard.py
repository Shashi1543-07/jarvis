import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os

class PostureGuard:
    def __init__(self):
        # Path to the model file
        model_path = os.path.join(os.getcwd(), 'models', 'mediapipe', 'pose_landmarker_lite.task')
        
        if not os.path.exists(model_path):
            print(f"PostureGuard Error: Model not found at {model_path}")
            self.landmarker = None
            return

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(base_options=base_options)
        self.landmarker = vision.PoseLandmarker.create_from_options(options)
        
        self.is_slouching = False
        self.slouch_counter = 0
        print("PostureGuard: Modern MediaPipe Tasks Landmarker initialized.")

    def check_posture(self, frame):
        """
        Analyzes the user's posture using modern MediaPipe Tasks.
        """
        if self.landmarker is None or frame is None:
            return {"success": False, "is_slouching": False}

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Detect pose
        detection_result = self.landmarker.detect(mp_image)

        if detection_result.pose_landmarks:
            # Key points: Nose (0), L Shoulder (11), R Shoulder (12)
            # Use landmark objects from the first detected person
            lm = detection_result.pose_landmarks[0]
            
            nose_y = lm[0].y
            shoulder_y = (lm[11].y + lm[12].y) / 2
            
            diff = shoulder_y - nose_y
            
            if diff < 0.12:  # Threshold for slouching
                self.slouch_counter += 1
            else:
                self.slouch_counter = 0

            self.is_slouching = self.slouch_counter > 15
            
            return {
                "success": True,
                "is_slouching": self.is_slouching,
                "diff": diff,
                "landmarks": lm
            }

        return {"success": False, "is_slouching": False}

    def draw_pose(self, frame, landmarks):
        # Drawing logic can be added here if needed
        return frame
