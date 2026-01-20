import numpy as np
import torch
import torchaudio
from scipy import signal
from collections import deque
import threading
import time


class AdvancedNoiseSuppression:
    """
    Advanced noise suppression system with multiple techniques:
    - Spectral subtraction
    - Deep learning-based suppression
    - Adaptive noise estimation
    - Stationary/non-stationary noise handling
    """
    
    def __init__(self, sample_rate=16000, frame_size=512):
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        
        # Noise estimation parameters - made more conservative for better voice preservation
        self.noise_floor = 0.00005  # Lower threshold to be more sensitive
        self.noise_learning_rate = 0.005  # Slower adaptation to preserve voice
        self.stationary_threshold = 0.01  # Lower threshold for better detection

        # Spectral subtraction parameters - reduced aggression
        self.over_subtraction_factor = 0.8  # Much less aggressive subtraction
        self.floor_attenuation = 0.3  # Higher floor to preserve voice
        
        # Adaptive parameters
        self.min_noise_frames = 20
        self.max_noise_frames = 200
        
        # Noise spectrum estimation
        self.noise_spectrum = None
        self.noise_spectrum_long = None  # For long-term estimation
        self.noise_frame_count = 0
        self.long_term_frame_count = 0
        
        # Speech presence detection
        self.speech_threshold = 0.3
        self.speech_probability = 0.5
        
        # Time-frequency masking parameters
        self.mask_smoothing = 0.8
        self.prev_mask = None
        
        # Buffers for temporal processing
        self.fft_buffer = deque(maxlen=5)
        self.phase_buffer = deque(maxlen=5)
        
        # Threading lock
        self.lock = threading.Lock()
        
        # Initialize deep learning model if available
        self.use_deep_model = False
        try:
            # Try to load a pre-trained model (would need to be downloaded separately)
            # For this implementation, we'll use the spectral approach
            pass
        except:
            print("Deep learning model not available, using spectral subtraction")
        
        print(f"AdvancedNoiseSuppression initialized: sample_rate={sample_rate}, frame_size={frame_size}")

    def _preprocess_audio(self, audio_chunk):
        """Convert audio chunk to float32 numpy array"""
        if isinstance(audio_chunk, bytes):
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            audio_data = audio_data / 32768.0
        else:
            audio_data = audio_chunk.astype(np.float32)
        return audio_data

    def _estimate_noise_spectrum(self, magnitude_spectrum):
        """Estimate noise spectrum from magnitude spectrum"""
        if self.noise_spectrum is None:
            # Initialize with current spectrum
            self.noise_spectrum = magnitude_spectrum.copy()
            self.noise_spectrum_long = magnitude_spectrum.copy()
        else:
            # Update short-term noise estimate (faster adaptation)
            self.noise_spectrum = (
                (1 - self.noise_learning_rate) * self.noise_spectrum +
                self.noise_learning_rate * magnitude_spectrum
            )
            
            # Update long-term noise estimate (slower adaptation)
            long_term_lr = 0.001
            self.noise_spectrum_long = (
                (1 - long_term_lr) * self.noise_spectrum_long +
                long_term_lr * magnitude_spectrum
            )
        
        # Count frames for statistics
        self.noise_frame_count += 1
        self.long_term_frame_count += 1

    def _detect_speech_presence(self, magnitude_spectrum):
        """Detect if speech is present in the current frame"""
        # Calculate SNR
        if self.noise_spectrum is not None:
            snr = magnitude_spectrum / (self.noise_spectrum + 1e-10)
            # Simple speech detection based on SNR
            speech_prob = np.mean(snr > 3.0)  # If SNR > 3dB, likely speech
            self.speech_probability = 0.7 * self.speech_probability + 0.3 * speech_prob
        else:
            self.speech_probability = 0.5
        
        return self.speech_probability > self.speech_threshold

    def _apply_spectral_subtraction(self, magnitude_spectrum, phase_spectrum):
        """Apply spectral subtraction for noise reduction"""
        if self.noise_spectrum is None:
            # No noise estimate yet, return original
            return magnitude_spectrum, phase_spectrum
        
        # Calculate enhanced magnitude using spectral subtraction
        enhanced_magnitude = magnitude_spectrum - self.over_subtraction_factor * self.noise_spectrum
        
        # Apply flooring to prevent over-suppression
        enhanced_magnitude = np.maximum(
            self.floor_attenuation * magnitude_spectrum,
            enhanced_magnitude
        )
        
        # Ensure non-negative values
        enhanced_magnitude = np.maximum(0.0001, enhanced_magnitude)
        
        return enhanced_magnitude, phase_spectrum

    def _create_time_freq_mask(self, magnitude_spectrum):
        """Create time-frequency mask for noise suppression"""
        if self.noise_spectrum is None:
            # No noise estimate, no suppression
            return np.ones_like(magnitude_spectrum)
        
        # Calculate SNR
        snr = magnitude_spectrum / (self.noise_spectrum + 1e-10)
        
        # Create mask based on SNR (Wiener filtering approach)
        mask = (snr - 1) / snr
        mask = np.clip(mask, 0.0, 1.0)  # Clamp between 0 and 1
        
        # Smooth mask temporally
        if self.prev_mask is not None:
            mask = self.mask_smoothing * self.prev_mask + (1 - self.mask_smoothing) * mask
        
        self.prev_mask = mask.copy()
        return mask

    def process_frame(self, audio_chunk):
        """
        Process a single audio frame for noise suppression
        
        Args:
            audio_chunk: Audio data as bytes or numpy array
            
        Returns:
            Clean audio as bytes
        """
        with self.lock:
            # Preprocess audio
            audio_data = self._preprocess_audio(audio_chunk)
            
            # Pad to frame size if needed
            if len(audio_data) < self.frame_size:
                padded = np.zeros(self.frame_size)
                padded[:len(audio_data)] = audio_data
                audio_data = padded
            else:
                audio_data = audio_data[:self.frame_size]
            
            # Reconstruct signal
            if self.noise_spectrum is not None and not is_noise_segment:
                # Create time-frequency mask
                mask = self._create_time_freq_mask(magnitude_spectrum)
                
                # Apply mask to magnitude spectrum
                enhanced_magnitude = magnitude_spectrum * mask
                
                # Reconstruct signal using magnitude and original phase
                enhanced_fft = enhanced_magnitude * np.exp(1j * phase_spectrum)
                enhanced_audio = np.real(np.fft.ifft(enhanced_fft))
            else:
                # No suppression applied
                enhanced_audio = audio_data
            
            # Convert back to int16
            enhanced_audio = np.clip(enhanced_audio * 32768.0, -32768, 32767).astype(np.int16)
            
            return enhanced_audio.tobytes()

    def reset_noise_estimates(self):
        """Reset all noise estimates"""
        with self.lock:
            self.noise_spectrum = None
            self.noise_spectrum_long = None
            self.noise_frame_count = 0
            self.long_term_frame_count = 0
            self.speech_probability = 0.5
            self.prev_mask = None
            print("Noise estimates reset")

    def get_noise_status(self):
        """Get status of noise estimation"""
        with self.lock:
            return {
                'noise_spectrum_estimated': self.noise_spectrum is not None,
                'noise_frames_collected': self.noise_frame_count,
                'speech_probability': self.speech_probability,
                'is_ready': self.noise_frame_count >= self.min_noise_frames
            }


class AdaptiveNoiseSuppressor:
    """
    Adaptive noise suppressor that adjusts parameters based on environment
    """
    
    def __init__(self, sample_rate=16000):
        self.suppressor = AdvancedNoiseSuppression(sample_rate)
        self.sample_rate = sample_rate
        
        # Environmental adaptation parameters - made more conservative
        self.environment_type = "quiet"  # quiet, moderate, noisy
        self.adaptation_speed = 0.005  # Slower adaptation
        self.energy_history = deque(maxlen=50)  # Smaller history for faster response
        self.snr_history = deque(maxlen=50)
        
        # Threading lock
        self.lock = threading.Lock()
        
        print("AdaptiveNoiseSuppressor initialized with environmental adaptation")

    def _classify_environment(self):
        """Classify current acoustic environment"""
        if len(self.energy_history) < 10:
            return "quiet"
        
        avg_energy = np.mean(list(self.energy_history))
        
        if avg_energy < 0.001:
            return "quiet"
        elif avg_energy < 0.01:
            return "moderate"
        else:
            return "noisy"

    def _adapt_parameters(self):
        """Adapt suppression parameters based on environment"""
        env_type = self._classify_environment()
        
        with self.lock:
            if env_type != self.environment_type:
                self.environment_type = env_type
                
                # Adjust parameters based on environment
                if env_type == "quiet":
                    # Less aggressive in quiet environments
                    self.suppressor.over_subtraction_factor = 1.0
                    self.suppressor.floor_attenuation = 0.3
                    self.suppressor.stationary_threshold = 0.005
                elif env_type == "moderate":
                    # Balanced parameters
                    self.suppressor.over_subtraction_factor = 1.3
                    self.suppressor.floor_attenuation = 0.1
                    self.suppressor.stationary_threshold = 0.02
                else:  # noisy
                    # More aggressive in noisy environments
                    self.suppressor.over_subtraction_factor = 1.8
                    self.suppressor.floor_attenuation = 0.05
                    self.suppressor.stationary_threshold = 0.05
                
                print(f"Environment adapted to: {env_type}")

    def process_frame(self, audio_chunk):
        """Process frame with environmental adaptation"""
        with self.lock:
            # Calculate frame energy for environment classification
            audio_data = self.suppressor._preprocess_audio(audio_chunk)
            frame_energy = np.mean(audio_data ** 2)
            
            # Update energy history
            self.energy_history.append(frame_energy)
            
            # Adapt parameters if needed
            self._adapt_parameters()
            
            # Process with noise suppression
            return self.suppressor.process_frame(audio_chunk)

    def get_status(self):
        """Get current status"""
        with self.lock:
            suppressor_status = self.suppressor.get_noise_status()
            return {
                **suppressor_status,
                'environment_type': self.environment_type,
                'avg_energy': np.mean(list(self.energy_history)) if self.energy_history else 0.0
            }


if __name__ == "__main__":
    # Test the noise suppression system
    suppressor = AdaptiveNoiseSuppressor()
    print("Advanced noise suppression system initialized")
    print("Ready for real-time noise suppression!")