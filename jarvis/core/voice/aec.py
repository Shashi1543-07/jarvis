import numpy as np


class AcousticEchoCanceller:
    """
    Simplified but strong echo canceller.
    Works well when TTS is much louder than microphone input.
    """

    def __init__(self, frame_size=512):
        self.frame_size = frame_size

    def process(self, mic_bytes, ref_bytes):
        if not ref_bytes:
            return mic_bytes

        try:
            mic = np.frombuffer(mic_bytes, dtype=np.int16).astype(np.float32)
            ref = np.frombuffer(ref_bytes, dtype=np.int16).astype(np.float32)

            L = min(len(mic), len(ref))
            mic = mic[:L]
            ref = ref[:L]

            # FFT
            mic_fft = np.fft.rfft(mic)
            ref_fft = np.fft.rfft(ref)

            mic_mag = np.abs(mic_fft)
            ref_mag = np.abs(ref_fft)
            phase = np.angle(mic_fft)

            # Adaptive over-subtraction (if TTS is loud, be aggressive)
            rms_ref = np.sqrt(np.mean(ref ** 2))
            alpha = 1.8 + (rms_ref / 6000.0)  # dynamic
            alpha = np.clip(alpha, 1.2, 4.0)

            clean_mag = np.maximum(0.0001, mic_mag - alpha * ref_mag)

            clean_fft = clean_mag * np.exp(1j * phase)
            clean = np.fft.irfft(clean_fft)

            return clean.astype(np.int16).tobytes()

        except Exception:
            return mic_bytes
