import numpy as np
from scipy import signal
import threading
import time
from collections import deque


class AdvancedAEC:
    """
    Advanced Acoustic Echo Canceller with double-talk detection and adaptive filtering.
    This implementation improves upon the basic AEC with more sophisticated algorithms.
    """
    
    def __init__(self, frame_size=512, filter_length=1024, step_size=0.025):
        self.frame_size = frame_size
        self.filter_length = filter_length
        self.step_size = step_size  # Learning rate
        
        # Adaptive filter coefficients
        self.h = np.zeros(filter_length)
        
        # Double-talk detector parameters
        self.dt_threshold = 0.1
        self.dt_counter = 0
        self.dt_max_count = 5
        self.double_talk_active = False
        
        # Echo path estimation
        self.echo_path_estimator = np.zeros(filter_length)
        self.echo_path_learning_rate = 0.001
        
        # Energy calculation for double-talk detection
        self.mic_energy_threshold = 0.001
        self.ref_energy_threshold = 0.001
        
        # Frequency domain processing for efficiency
        self.fft_size = frame_size * 2
        self.freq_buffer = np.zeros(self.fft_size, dtype=complex)
        
        # Memory for delay compensation
        self.ref_delay_buffer = np.zeros(filter_length)
        self.delay_pos = 0
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Statistics for monitoring
        self.stats = {
            'echo_return_loss': 0.0,
            'double_talk_events': 0,
            'adaptation_stops': 0,
            'last_update': time.time()
        }
        
        print(f"AdvancedAEC initialized: frame_size={frame_size}, filter_length={filter_length}")

    def _calculate_energy(self, audio_signal):
        """Calculate RMS energy of audio signal"""
        if isinstance(audio_signal, bytes):
            audio_data = np.frombuffer(audio_signal, dtype=np.int16).astype(np.float32)
            audio_data = audio_data / 32768.0
        else:
            audio_data = audio_signal.astype(np.float32)
        
        return float(np.mean(audio_data ** 2))

    def _double_talk_detection(self, mic_power, ref_power):
        """
        Detect double-talk situation where both near-end and far-end speak
        """
        # Calculate signal-to-noise ratio
        snr = mic_power / (ref_power + 1e-10)
        
        # Double-talk if both signals are strong and SNR is moderate
        double_talk = (mic_power > self.mic_energy_threshold and 
                      ref_power > self.ref_energy_threshold and
                      0.1 < snr < 10.0)  # Both active, neither dominant
        
        return double_talk

    def _update_statistics(self, mic_power, ref_power, echo_reduction_db):
        """Update AEC performance statistics"""
        self.stats['echo_return_loss'] = echo_reduction_db
        self.stats['last_update'] = time.time()

    def process(self, mic_signal, ref_signal):
        """
        Process microphone and reference signals to remove echo
        Returns: (clean_signal, echo_reduction_db)
        """
        with self.lock:
            # Convert to float32
            if isinstance(mic_signal, bytes):
                mic = np.frombuffer(mic_signal, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                mic = mic_signal.astype(np.float32)
                
            if isinstance(ref_signal, bytes):
                ref = np.frombuffer(ref_signal, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                ref = ref_signal.astype(np.float32)
            
            # Ensure same length
            min_len = min(len(mic), len(ref))
            mic = mic[:min_len]
            ref = ref[:min_len]
            
            # Calculate powers for double-talk detection (frame-level)
            mic_power = np.mean(mic ** 2)
            ref_power = np.mean(ref ** 2)
            
            # Double-talk detection
            current_double_talk = self._double_talk_detection(mic_power, ref_power)
            
            if current_double_talk:
                self.dt_counter += 1
                if self.dt_counter > self.dt_max_count:
                    self.double_talk_active = True
                    self.stats['double_talk_events'] += 1
                    self.stats['adaptation_stops'] += 1
            else:
                self.dt_counter = max(0, self.dt_counter - 1)
                if self.dt_counter == 0:
                    self.double_talk_active = False
            
            # --- Time-Domain NLMS (Normalized Least Mean Squares) AEC ---
            # This is more robust for short frames than circular FFT convolution
            
            clean_signal_float = np.zeros(min_len)
            
            for i in range(min_len):
                # Shift reference buffer
                self.ref_delay_buffer = np.roll(self.ref_delay_buffer, 1)
                self.ref_delay_buffer[0] = ref[i]
                
                # Estimate echo: y_hat = h . x
                echo_estimate = np.dot(self.h, self.ref_delay_buffer)
                
                # Error signal: e = d - y_hat
                error = mic[i] - echo_estimate
                clean_signal_float[i] = error
                
                # Double-talk detection logic (for conditional adaptation)
                # mic_pwr = mic[i]**2 # Instantaneous mic power
                # ref_pwr = self.ref_delay_buffer[0]**2 # Instantaneous ref power
                
                if not self.double_talk_active:
                    # Update filter coefficients: h = h + step * e * x / (||x||^2 + eps)
                    # Using a small regularization term (1e-6) to avoid division by zero
                    norm_factor = self.ref_delay_buffer @ self.ref_delay_buffer + 1e-6
                    self.h += (self.step_size * error * self.ref_delay_buffer) / norm_factor
                    
                    # Periodic leak to prevent drift
                    if i % 100 == 0:
                        self.h *= 0.9999
            
            # Inverse FFT to get cleaned signal is no longer needed
            clean_signal = clean_signal_float
            
            # Calculate echo reduction for stats
            original_power = mic_power
            residual_power = np.mean(clean_signal ** 2) + 1e-10
            echo_reduction_db = 10 * np.log10(original_power / residual_power)
            
            # Update statistics
            self._update_statistics(mic_power, ref_power, echo_reduction_db)
            
            # Convert back to int16
            clean_signal = np.clip(clean_signal * 32768.0, -32768, 32767).astype(np.int16)
            return clean_signal.tobytes(), echo_reduction_db

    def get_statistics(self):
        """Get current AEC statistics"""
        with self.lock:
            return self.stats.copy()

    def reset(self):
        """Reset AEC state"""
        with self.lock:
            self.h.fill(0)
            self.echo_path_estimator.fill(0)
            self.dt_counter = 0
            self.double_talk_active = False
            self.stats = {
                'echo_return_loss': 0.0,
                'double_talk_events': 0,
                'adaptation_stops': 0,
                'last_update': time.time()
            }

    def set_adaptation_rate(self, rate):
        """Adjust adaptation rate (learning rate)"""
        with self.lock:
            self.step_size = max(0.001, min(0.1, rate))


class EnhancedAECWithNR:
    """
    Enhanced AEC that also includes noise reduction capabilities
    """
    
    def __init__(self, frame_size=512, filter_length=1024):
        self.aec = AdvancedAEC(frame_size, filter_length)

        # Noise reduction parameters
        self.noise_floor = 0.0001
        self.nr_attenuation = 0.7  # How much to attenuate noise
        self.frame_size = frame_size  # Store frame size for proper initialization

        # Spectral noise estimation
        self.noise_spectrum = None
        self.noise_estimation_frames = 0
        self.max_noise_frames = 100

        # Lock for thread safety
        self.lock = threading.Lock()

        print("EnhancedAECWithNR initialized with noise reduction")

    def process_with_noise_reduction(self, mic_signal, ref_signal):
        """
        Process signal with both AEC and noise reduction
        """
        with self.lock:
            # First, apply AEC
            clean_signal, echo_reduction_db = self.aec.process(mic_signal, ref_signal)
            
            # Convert to float for noise reduction
            if isinstance(clean_signal, bytes):
                audio_data = np.frombuffer(clean_signal, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_data = clean_signal.astype(np.float32)
            
            # Apply noise reduction (Spectral Subtraction)
            if len(audio_data) > 0:
                # Estimate noise spectrum during quiet periods
                current_power = np.mean(audio_data ** 2)
                
                if current_power < self.noise_floor and self.noise_estimation_frames < self.max_noise_frames:
                    # This is likely noise-only segment, update noise estimate
                    fft_data = np.fft.fft(audio_data)
                    magnitude = np.abs(fft_data)
                    
                    if self.noise_spectrum is None:
                        self.noise_spectrum = magnitude
                    else:
                        # Exponential averaging
                        self.noise_spectrum = 0.9 * self.noise_spectrum + 0.1 * magnitude
                    
                    self.noise_estimation_frames += 1
                
                # Apply spectral subtraction if we have a noise estimate
                if self.noise_spectrum is not None:
                    fft_data = np.fft.fft(audio_data)
                    magnitude = np.abs(fft_data)
                    phase = np.angle(fft_data)
                    
                    # Subtract noise spectrum with attenuation
                    enhanced_magnitude = np.maximum(
                        0.0001,  # Floor to avoid division by zero
                        magnitude - self.nr_attenuation * self.noise_spectrum
                    )
                    
                    # Reconstruct signal
                    enhanced_fft = enhanced_magnitude * np.exp(1j * phase)
                    audio_data = np.real(np.fft.ifft(enhanced_fft))
            
            # Convert back to int16
            audio_data = np.clip(audio_data * 32768.0, -32768, 32767).astype(np.int16)
            return audio_data.tobytes(), echo_reduction_db

    def get_statistics(self):
        """Get statistics from both AEC and noise reduction"""
        aec_stats = self.aec.get_statistics()
        with self.lock:
            nr_stats = {
                'noise_spectrum_estimated': self.noise_spectrum is not None,
                'noise_estimation_progress': min(1.0, self.noise_estimation_frames / self.max_noise_frames)
            }
            return {**aec_stats, **nr_stats}


if __name__ == "__main__":
    # Test the enhanced AEC
    aec = EnhancedAECWithNR()
    print("Enhanced AEC with noise reduction initialized")
    print("Ready for real-time audio processing!")