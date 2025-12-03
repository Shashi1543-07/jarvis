"""
Emotion Detector - Facial emotion recognition using DeepFace
Detects emotions: happy, sad, angry, neutral, surprise, fear, disgust
"""

import cv2
import numpy as np

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("[EmotionDetector] Warning: deepface not installed. Emotion detection disabled.")


class EmotionDetector:
    """DeepFace-based emotion recognition"""
    
    def __init__(self):
        """Initialize Emotion Detector"""
        if not DEEPFACE_AVAILABLE:
            print("[EmotionDetector] DeepFace not available")
            return
        
        print("[EmotionDetector] Initialized (will analyze on request)")
    
    def detect_emotion(self, frame):
        """
        Detect emotion from face in frame
        
        Args:
            frame: OpenCV BGR frame
            
        Returns:
            dict with emotion, confidence, and additional attributes
        """
        if not DEEPFACE_AVAILABLE:
            return {
                'emotion': 'unknown',
                'confidence': 0.0,
                'error': 'DeepFace not available'
            }
        
        try:
            # DeepFace.analyze requires RGB or BGR, it handles conversion internally
            # enforce_detection=False allows it to work even if face detection is uncertain
            analysis = DeepFace.analyze(
                frame,
                actions=['emotion', 'age', 'gender'],
                enforce_detection=False,
                silent=True
            )
            
            # Handle both single face and multiple faces return format
            if isinstance(analysis, list):
                if len(analysis) == 0:
                    return {
                        'emotion': 'unknown',
                        'confidence': 0.0,
                        'error': 'No face detected'
                    }
                analysis = analysis[0]  # Use first face
            
            # Get dominant emotion
            emotion_scores = analysis.get('emotion', {})
            dominant_emotion = analysis.get('dominant_emotion', 'unknown')
            
            # Get confidence for dominant emotion
            confidence = emotion_scores.get(dominant_emotion, 0.0) / 100.0  # Convert to 0-1
            
            # Additional attributes
            age = analysis.get('age', 'unknown')
            gender = analysis.get('dominant_gender', 'unknown')
            
            return {
                'emotion': dominant_emotion,
                'confidence': confidence,
                'all_emotions': emotion_scores,
                'age': age,
                'gender': gender,
                'success': True
            }
            
        except Exception as e:
            # Common errors: no face detected, model loading issues
            error_msg = str(e)
            
            if 'Face could not be detected' in error_msg or 'no face' in error_msg.lower():
                return {
                    'emotion': 'unknown',
                    'confidence': 0.0,
                    'error': 'No face detected in frame'
                }
            
            return {
                'emotion': 'unknown',
                'confidence': 0.0,
                'error': f'Emotion detection failed: {error_msg}'
            }
    
    def get_emotion_label(self, emotion, confidence):
        """
        Format emotion for user-friendly display
        
        Args:
            emotion: Emotion name
            confidence: Confidence score (0-1)
            
        Returns:
            Formatted string
        """
        confidence_pct = int(confidence * 100)
        
        if confidence < 0.5:
            return f"Possibly {emotion} ({confidence_pct}% confident)"
        elif confidence < 0.7:
            return f"{emotion.capitalize()} ({confidence_pct}% confident)"
        else:
            return f"Clearly {emotion} ({confidence_pct}% confident)"
    
    def analyze_multiple_frames(self, frames):
        """
        Analyze emotion across multiple frames for more stable results
        
        Args:
            frames: List of OpenCV BGR frames
            
        Returns:
            dict with averaged emotion results
        """
        if not frames:
            return {
                'emotion': 'unknown',
                'confidence': 0.0,
                'error': 'No frames provided'
            }
        
        emotion_counts = {}
        total_confidence = 0.0
        successful_frames = 0
        
        for frame in frames:
            result = self.detect_emotion(frame)
            
            if result.get('success'):
                emotion = result['emotion']
                confidence = result['confidence']
                
                if emotion not in emotion_counts:
                    emotion_counts[emotion] = []
                
                emotion_counts[emotion].append(confidence)
                total_confidence += confidence
                successful_frames += 1
        
        if successful_frames == 0:
            return {
                'emotion': 'unknown',
                'confidence': 0.0,
                'error': 'No successful detections'
            }
        
        # Find most common emotion weighted by confidence
        dominant_emotion = max(emotion_counts.items(), 
                             key=lambda x: sum(x[1]) / len(x[1]))[0]
        
        avg_confidence = sum(emotion_counts[dominant_emotion]) / len(emotion_counts[dominant_emotion])
        
        return {
            'emotion': dominant_emotion,
            'confidence': avg_confidence,
            'frames_analyzed': successful_frames,
            'success': True
        }
