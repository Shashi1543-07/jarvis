"""
Face Manager - Handles face recognition with persistent memory
Uses face_recognition library to identify and remember people
"""

import os
import pickle
import numpy as np
import cv2
import face_recognition
from pathlib import Path


class FaceManager:
    """Manages face recognition with persistent storage"""
    
    def __init__(self, faces_dir="faces"):
        """
        Initialize Face Manager
        
        Args:
            faces_dir: Directory containing face images (relative to project root)
        """
        # Get project root (3 levels up from core/vision/)
        project_root = Path(__file__).parent.parent.parent.parent
        self.faces_dir = project_root / faces_dir
        self.encodings_file = self.faces_dir / "face_encodings.pkl"
        
        # Ensure faces directory exists
        self.faces_dir.mkdir(exist_ok=True)
        
        # Cache for face encodings
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Load existing faces
        self._load_faces()
        
        print(f"[FaceManager] Initialized with {len(self.known_face_names)} known faces")
    
    def _load_faces(self):
        """Load face encodings from cache or rebuild from images"""
        # Try to load from cache first
        if self.encodings_file.exists():
            try:
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data['encodings']
                    self.known_face_names = data['names']
                print(f"[FaceManager] Loaded {len(self.known_face_names)} faces from cache")
                return
            except Exception as e:
                print(f"[FaceManager] Failed to load cache: {e}")
        
        # Rebuild from image files
        self._rebuild_encodings()
    
    def _rebuild_encodings(self):
        """Rebuild face encodings from image files in faces/ directory"""
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Scan for image files
        image_extensions = ['.jpg', '.jpeg', '.png']
        face_images = []
        
        for ext in image_extensions:
            face_images.extend(self.faces_dir.glob(f"*{ext}"))
        
        print(f"[FaceManager] Found {len(face_images)} face images, encoding...")
        
        for image_path in face_images:
            try:
                # Get person name from filename (without extension)
                person_name = image_path.stem
                
                # Load image
                image = face_recognition.load_image_file(str(image_path))
                
                # Get face encoding (use first face found)
                encodings = face_recognition.face_encodings(image)
                
                if encodings:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_names.append(person_name)
                    print(f"[FaceManager] ✓ Encoded: {person_name}")
                else:
                    print(f"[FaceManager] ✗ No face found in: {person_name}")
                    
            except Exception as e:
                print(f"[FaceManager] Error encoding {image_path.name}: {e}")
        
        # Save to cache
        self._save_cache()
    
    def _save_cache(self):
        """Save encodings to cache file"""
        try:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump({
                    'encodings': self.known_face_encodings,
                    'names': self.known_face_names
                }, f)
            print(f"[FaceManager] Saved cache with {len(self.known_face_names)} faces")
        except Exception as e:
            print(f"[FaceManager] Failed to save cache: {e}")
    
    def recognize_faces(self, frame):
        """
        Recognize faces in a frame
        
        Args:
            frame: OpenCV BGR frame
            
        Returns:
            List of dicts with keys: name, location, confidence
        """
        if not self.known_face_encodings:
            return []
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize frame for faster processing (1/4 size)
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
        
        # Find faces and encodings
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)
        
        results = []
        
        for encoding, location in zip(face_encodings, face_locations):
            # Compare with known faces
            distances = face_recognition.face_distance(self.known_face_encodings, encoding)
            
            if len(distances) > 0:
                best_match_idx = np.argmin(distances)
                confidence = 1 - distances[best_match_idx]
                
                # Threshold for recognition (0.6 = 60% similar)
                if confidence > 0.6:
                    name = self.known_face_names[best_match_idx]
                else:
                    name = "Unknown"
            else:
                name = "Unknown"
                confidence = 0.0
            
            # Scale back location to original frame size
            top, right, bottom, left = location
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            
            results.append({
                'name': name,
                'location': (top, right, bottom, left),
                'confidence': float(confidence)
            })
        
        return results
    
    def learn_face(self, frame, person_name):
        """
        Learn a new face from the current frame
        
        Args:
            frame: OpenCV BGR frame
            person_name: Name to associate with this face
            
        Returns:
            dict with success status and message
        """
        try:
            # Convert to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if not face_locations:
                return {
                    'success': False,
                    'message': 'No face detected in frame. Please look at the camera.'
                }
            
            if len(face_locations) > 1:
                return {
                    'success': False,
                    'message': 'Multiple faces detected. Please ensure only one person is visible.'
                }
            
            # Get encoding
            encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            if not encodings:
                return {
                    'success': False,
                    'message': 'Could not encode face. Please try again.'
                }
            
            # Save face image
            image_path = self.faces_dir / f"{person_name}.jpg"
            cv2.imwrite(str(image_path), frame)
            
            # Add to known faces
            self.known_face_encodings.append(encodings[0])
            self.known_face_names.append(person_name)
            
            # Update cache
            self._save_cache()
            
            return {
                'success': True,
                'message': f"Successfully learned {person_name}'s face. I'll remember them."
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error learning face: {str(e)}"
            }
    
    def get_known_people(self):
        """Return list of all known people"""
        return self.known_face_names.copy()
    
    def forget_person(self, person_name):
        """Remove a person from memory"""
        try:
            if person_name not in self.known_face_names:
                return {
                    'success': False,
                    'message': f"I don't know anyone named {person_name}."
                }
            
            # Remove from lists
            idx = self.known_face_names.index(person_name)
            del self.known_face_encodings[idx]
            del self.known_face_names[idx]
            
            # Delete image file
            image_path = self.faces_dir / f"{person_name}.jpg"
            if image_path.exists():
                image_path.unlink()
            
            # Update cache
            self._save_cache()
            
            return {
                'success': True,
                'message': f"I've forgotten {person_name}."
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error forgetting person: {str(e)}"
            }
