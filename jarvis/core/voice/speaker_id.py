import torch
import numpy as np
import torchaudio
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict, deque
import threading
import pickle
import os
from typing import Optional, Tuple, Dict, List


class SpeakerEmbeddingExtractor:
    """
    Extracts speaker embeddings using a pre-trained model.
    For this implementation, we'll use a simplified approach that could be
    replaced with a full model like ECAPA-TDNN in production.
    """
    
    def __init__(self):
        self.embedding_dim = 192  # Standard dimension for speaker embeddings
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Audio preprocessing
        self.mfcc_transform = torchaudio.transforms.MFCC(
            sample_rate=16000,
            n_mfcc=40,
            melkwargs={'n_fft': 512, 'hop_length': 160, 'n_mels': 40}
        )
        
        # Initialize a simple model (in practice, use pre-trained ECAPA-TDNN)
        self._init_simple_model()
        
        print(f"SpeakerEmbeddingExtractor initialized on {self.device}")
    
    def _init_simple_model(self):
        """
        Initialize a simple model for demonstration.
        In production, load a pre-trained ECAPA-TDNN or similar model.
        """
        # This is a placeholder - in real implementation, you'd load a pre-trained model
        # For example: torch.hub.load('mravanelli/pytorch-kaldi', 'tdnn', pretrained=True)
        self.model = None
        print("Using simplified embedding extraction (replace with pre-trained model for production)")
    
    def extract_embedding(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Extract speaker embedding from audio data.
        
        Args:
            audio_data: Audio as numpy array or bytes
            
        Returns:
            Speaker embedding vector (192-dimensional)
        """
        if isinstance(audio_data, bytes):
            audio_tensor = torch.FloatTensor(
                np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            ) / 32768.0
        else:
            audio_tensor = torch.FloatTensor(audio_data)
        
        # Ensure audio is properly shaped
        if audio_tensor.dim() == 1:
            audio_tensor = audio_tensor.unsqueeze(0)
        
        # For this implementation, we'll use MFCC statistics as a simple embedding
        # In production, use a proper speaker embedding model
        try:
            # Extract MFCC features
            mfcc_features = self.mfcc_transform(audio_tensor)
            
            # Calculate statistics over time dimension
            mean_features = torch.mean(mfcc_features, dim=-1)
            std_features = torch.std(mfcc_features, dim=-1)
            
            # Concatenate mean and std to form embedding
            embedding = torch.cat([mean_features, std_features], dim=-1)
            
            # Ensure embedding is the right size
            if embedding.shape[-1] < self.embedding_dim:
                # Pad with zeros
                padding = torch.zeros(self.embedding_dim - embedding.shape[-1])
                embedding = torch.cat([embedding.flatten(), padding])
            elif embedding.shape[-1] > self.embedding_dim:
                # Truncate
                embedding = embedding.flatten()[:self.embedding_dim]
            else:
                embedding = embedding.flatten()
            
            return embedding.cpu().numpy().astype(np.float32)
            
        except Exception as e:
            print(f"Error extracting embedding: {e}")
            # Return a default embedding in case of error
            return np.random.rand(self.embedding_dim).astype(np.float32)


class SpeakerRecognizer:
    """
    Main speaker recognition system that handles enrollment and verification.
    """
    
    def __init__(self, verification_threshold: float = 0.7):
        self.embedder = SpeakerEmbeddingExtractor()
        self.registered_speakers: Dict[str, np.ndarray] = {}
        self.verification_threshold = verification_threshold
        self.enrollment_sessions: Dict[str, List[np.ndarray]] = {}
        
        # Anti-spoofing parameters
        self.anti_spoofing_enabled = True
        self.min_enrollment_samples = 3
        self.max_registration_attempts = 5
        
        # Thread safety
        self.lock = threading.Lock()
        
        print(f"SpeakerRecognizer initialized with threshold: {verification_threshold}")
    
    def enroll_speaker(self, speaker_id: str, audio_samples: List[np.ndarray]) -> bool:
        """
        Enroll a new speaker with multiple audio samples.
        
        Args:
            speaker_id: Unique identifier for the speaker
            audio_samples: List of audio samples from the speaker
            
        Returns:
            True if enrollment successful, False otherwise
        """
        with self.lock:
            if len(audio_samples) < self.min_enrollment_samples:
                print(f"Need at least {self.min_enrollment_samples} samples for enrollment")
                return False
            
            # Extract embeddings for all samples
            embeddings = []
            for audio in audio_samples:
                try:
                    emb = self.embedder.extract_embedding(audio)
                    embeddings.append(emb)
                except Exception as e:
                    print(f"Failed to extract embedding from sample: {e}")
                    continue
            
            if len(embeddings) < self.min_enrollment_samples:
                print(f"Not enough valid embeddings extracted for enrollment")
                return False
            
            # Average embeddings for more robust representation
            avg_embedding = np.mean(embeddings, axis=0)
            
            # Store the registered speaker
            self.registered_speakers[speaker_id] = avg_embedding.astype(np.float32)
            
            print(f"Speaker '{speaker_id}' enrolled successfully")
            return True
    
    def verify_speaker(self, audio_data: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Verify if the speaker in the audio matches any registered speaker.
        
        Args:
            audio_data: Audio data to verify
            
        Returns:
            Tuple of (speaker_id, confidence) or (None, 0.0) if no match
        """
        with self.lock:
            if not self.registered_speakers:
                return None, 0.0
            
            # Extract embedding from input audio
            try:
                candidate_embedding = self.embedder.extract_embedding(audio_data)
            except Exception as e:
                print(f"Error extracting embedding for verification: {e}")
                return None, 0.0
            
            best_match = None
            best_confidence = 0.0
            
            # Compare against all registered speakers
            for speaker_id, stored_embedding in self.registered_speakers.items():
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    candidate_embedding.reshape(1, -1),
                    stored_embedding.reshape(1, -1)
                )[0][0]
                
                if similarity > best_confidence and similarity >= self.verification_threshold:
                    best_confidence = similarity
                    best_match = speaker_id
            
            return best_match, float(best_confidence)
    
    def identify_speaker(self, audio_data: np.ndarray) -> Tuple[Optional[str], Dict[str, float]]:
        """
        Identify speaker among all registered speakers.
        
        Args:
            audio_data: Audio data to identify
            
        Returns:
            Tuple of (best_match_speaker_id, all_similarities_dict)
        """
        with self.lock:
            if not self.registered_speakers:
                return None, {}
            
            try:
                candidate_embedding = self.embedder.extract_embedding(audio_data)
            except Exception as e:
                print(f"Error extracting embedding for identification: {e}")
                return None, {}
            
            similarities = {}
            
            # Calculate similarity with all registered speakers
            for speaker_id, stored_embedding in self.registered_speakers.items():
                similarity = cosine_similarity(
                    candidate_embedding.reshape(1, -1),
                    stored_embedding.reshape(1, -1)
                )[0][0]
                
                similarities[speaker_id] = float(similarity)
            
            # Find the best match
            if similarities:
                best_match = max(similarities.keys(), key=lambda k: similarities[k])
                best_score = similarities[best_match]
                
                if best_score >= self.verification_threshold:
                    return best_match, similarities
            
            return None, similarities
    
    def remove_speaker(self, speaker_id: str) -> bool:
        """Remove a registered speaker."""
        with self.lock:
            if speaker_id in self.registered_speakers:
                del self.registered_speakers[speaker_id]
                if speaker_id in self.enrollment_sessions:
                    del self.enrollment_sessions[speaker_id]
                print(f"Speaker '{speaker_id}' removed")
                return True
            return False
    
    def list_registered_speakers(self) -> List[str]:
        """List all registered speaker IDs."""
        with self.lock:
            return list(self.registered_speakers.keys())
    
    def get_speaker_count(self) -> int:
        """Get the number of registered speakers."""
        with self.lock:
            return len(self.registered_speakers)
    
    def save_model(self, filepath: str):
        """Save the registered speakers to a file."""
        with self.lock:
            data = {
                'registered_speakers': self.registered_speakers,
                'verification_threshold': self.verification_threshold
            }
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            print(f"Speaker model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load registered speakers from a file."""
        with self.lock:
            if not os.path.exists(filepath):
                print(f"Model file {filepath} does not exist")
                return False
            
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.registered_speakers = data.get('registered_speakers', {})
            self.verification_threshold = data.get('verification_threshold', 0.7)
            
            print(f"Speaker model loaded from {filepath}")
            print(f"Loaded {len(self.registered_speakers)} speakers")
            return True


class SpeakerAuthenticator:
    """
    Higher-level class that integrates speaker recognition into the voice system.
    """
    
    def __init__(self, verification_threshold: float = 0.7):
        self.recognizer = SpeakerRecognizer(verification_threshold)
        self.current_speaker = None
        self.last_verification_time = 0
        self.verification_timeout = 300  # 5 minutes
        
        # Access control
        self.allowed_speakers = set()  # Empty means allow all
        self.access_logs = deque(maxlen=100)
        
        print("SpeakerAuthenticator initialized")
    
    def authenticate(self, audio_data: np.ndarray) -> Tuple[bool, Optional[str], float]:
        """
        Authenticate speaker and return authorization status.
        
        Args:
            audio_data: Audio data to authenticate
            
        Returns:
            Tuple of (is_authenticated, speaker_id, confidence)
        """
        speaker_id, confidence = self.recognizer.verify_speaker(audio_data)
        
        if speaker_id:
            # Check if speaker is allowed (if access control is enabled)
            is_allowed = (not self.allowed_speakers or 
                         speaker_id in self.allowed_speakers)
            
            if is_allowed:
                self.current_speaker = speaker_id
                self.last_verification_time = 0  # Reset timeout tracking
                
                # Log access
                self.access_logs.append({
                    'speaker_id': speaker_id,
                    'confidence': confidence,
                    'timestamp': 0,  # Would be actual timestamp
                    'granted': True
                })
                
                return True, speaker_id, confidence
            else:
                # Speaker recognized but not authorized
                self.access_logs.append({
                    'speaker_id': speaker_id,
                    'confidence': confidence,
                    'timestamp': 0,
                    'granted': False
                })
                
                return False, speaker_id, confidence
        else:
            # Speaker not recognized
            self.access_logs.append({
                'speaker_id': 'unknown',
                'confidence': confidence,
                'timestamp': 0,
                'granted': False
            })
            
            return False, None, 0.0
    
    def enroll_current_speaker(self, speaker_id: str, audio_samples: List[np.ndarray]) -> bool:
        """Enroll the current speaker."""
        return self.recognizer.enroll_speaker(speaker_id, audio_samples)
    
    def add_allowed_speaker(self, speaker_id: str):
        """Add a speaker to the allowed list."""
        self.allowed_speakers.add(speaker_id)
    
    def remove_allowed_speaker(self, speaker_id: str):
        """Remove a speaker from the allowed list."""
        self.allowed_speakers.discard(speaker_id)
    
    def is_access_control_enabled(self) -> bool:
        """Check if access control is enabled."""
        return len(self.allowed_speakers) > 0
    
    def get_access_logs(self, count: int = 10) -> List[dict]:
        """Get recent access logs."""
        return list(self.access_logs)[-count:]


if __name__ == "__main__":
    # Test the speaker recognition system
    recognizer = SpeakerRecognizer()
    
    print("Speaker recognition system test:")
    print(f"Registered speakers: {recognizer.list_registered_speakers()}")
    print("System ready for enrollment and verification!")