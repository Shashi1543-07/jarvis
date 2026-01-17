import numpy as np
import noisereduce as nr
from scipy import signal
import librosa

class AudioPreprocessor:
    """
    Preprocesses audio for optimal speech recognition.
    - Noise reduction
    - Normalization
    - Resampling to 16kHz mono
    - Silence trimming
    """
    
    def __init__(self, target_sample_rate=16000):
        self.target_sample_rate = target_sample_rate
        self.noise_profile = None
        self.noise_profile_frames = []
        self.learning_noise = True
        self.noise_samples_needed = 10  # ~0.3 seconds of noise profile
        
        print(f"AudioPreprocessor initialized (target: {target_sample_rate}Hz)")
    
    def learn_noise_profile(self, audio_chunk):
        """Learn background noise profile from initial frames"""
        if self.learning_noise and len(self.noise_profile_frames) < self.noise_samples_needed:
            self.noise_profile_frames.append(audio_chunk)
            
            if len(self.noise_profile_frames) >= self.noise_samples_needed:
                # Combine all noise frames
                combined = b''.join(self.noise_profile_frames)
                self.noise_profile = combined
                self.learning_noise = False
                print("AudioPreprocessor: Noise profile learned")
    
    def bytes_to_float32(self, audio_bytes):
        """Convert 16-bit PCM bytes to float32 numpy array"""
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        return audio_float32
    
    def float32_to_bytes(self, audio_float32):
        """Convert float32 numpy array back to 16-bit PCM bytes"""
        audio_int16 = (audio_float32 * 32768.0).astype(np.int16)
        return audio_int16.tobytes()
    
    def normalize_audio(self, audio_float32):
        """Normalize audio to consistent volume level"""
        # Calculate RMS (Root Mean Square) energy
        rms = np.sqrt(np.mean(audio_float32**2))
        
        if rms > 0:
            # Target RMS level (adjust for comfortable listening)
            target_rms = 0.1
            normalization_factor = target_rms / rms
            
            # Limit amplification to avoid clipping
            normalization_factor = min(normalization_factor, 3.0)
            
            normalized = audio_float32 * normalization_factor
            
            # Clip to prevent overflow
            normalized = np.clip(normalized, -1.0, 1.0)
            return normalized
        
        return audio_float32
    
    def denoise_audio(self, audio_float32):
        """Remove background noise using spectral gating"""
        if self.noise_profile is None:
            # No noise profile yet, return as-is
            return audio_float32
        
        try:
            # Use noisereduce with learned noise profile
            noise_float = self.bytes_to_float32(self.noise_profile)
            
            # Perform noise reduction
            denoised = nr.reduce_noise(
                y=audio_float32,
                sr=self.target_sample_rate,
                y_noise=noise_float,
                stationary=True,
                prop_decrease=0.8  # 80% noise reduction
            )
            
            return denoised
        except Exception as e:
            print(f"AudioPreprocessor: Denoising failed - {e}")
            return audio_float32
    
    def trim_silence(self, audio_float32, threshold=0.01):
        """Remove leading and trailing silence"""
        # Find non-silent regions
        non_silent = np.abs(audio_float32) > threshold
        
        if not np.any(non_silent):
            # All silence, return as-is
            return audio_float32
        
        # Find first and last non-silent indices
        non_silent_indices = np.where(non_silent)[0]
        start_idx = max(0, non_silent_indices[0] - 100)  # Keep small buffer
        end_idx = min(len(audio_float32), non_silent_indices[-1] + 100)
        
        return audio_float32[start_idx:end_idx]
    
    def validate_audio_quality(self, audio_float32):
        """Check if audio has sufficient energy (not just noise)"""
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_float32**2))
        
        # Minimum energy threshold
        min_energy = 0.005
        
        if rms < min_energy:
            return False
        
        # Check for NaN or Inf
        if not np.isfinite(audio_float32).all():
            return False
        
        return True
    
    def process_chunk(self, audio_chunk_bytes):
        """
        Process a single audio chunk in real-time.
        Used during buffering phase.
        """
        # Learn noise profile if still learning
        if self.learning_noise:
            self.learn_noise_profile(audio_chunk_bytes)
            return audio_chunk_bytes  # Return unprocessed during learning
        
        # Convert to float32
        audio_float = self.bytes_to_float32(audio_chunk_bytes)
        
        # Normalize (cheap operation, can do per-chunk)
        audio_float = self.normalize_audio(audio_float)
        
        # Convert back to bytes
        return self.float32_to_bytes(audio_float)
    
    def process_complete_audio(self, audio_buffer_list):
        """
        Process complete buffered audio before transcription.
        This is where we do the heavy preprocessing.
        
        Args:
            audio_buffer_list: List of audio chunk bytes
        
        Returns:
            Processed audio as bytes
        """
        # Combine all chunks
        combined_bytes = b''.join(audio_buffer_list)
        
        # Convert to float32
        audio_float = self.bytes_to_float32(combined_bytes)
        
        # 1. Denoise (most important for accuracy)
        audio_float = self.denoise_audio(audio_float)
        
        # 2. Normalize volume   
    
        audio_float = self.normalize_audio(audio_float)
        
        # 3. Trim silence
        audio_float = self.trim_silence(audio_float)
        
        # 4. Validate quality
        if not self.validate_audio_quality(audio_float):
            print("AudioPreprocessor: Low quality audio detected")
            return None
        
        # Convert back to bytes
        return self.float32_to_bytes(audio_float)
    
    def reset_noise_profile(self):
        """Reset noise profile (useful if environment changes)"""
        self.noise_profile = None
        self.noise_profile_frames = []
        self.learning_noise = True
        print("AudioPreprocessor: Noise profile reset")
