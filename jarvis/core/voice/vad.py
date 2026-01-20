import torch
import numpy as np
from collections import deque


class VoiceActivityDetector:
    def __init__(self):
        # Load Silero VAD
        self.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True
        )

        (_, _, _, _, _) = utils

        self.sample_rate = 16000

        # Thresholds - made more sensitive
        self.base_threshold = 0.10  # Lowered for better sensitivity (was 0.15)
        self.dynamic_threshold = self.base_threshold

        # Background noise learning
        self.noise_probs = []
        self.noise_frames_needed = 15  # Faster learning (was 20)
        self.noise_learned = False

        # Smoothing (reduces false positives but kept shorter for responsiveness)
        self.smooth_window = deque(maxlen=3)  # Shorter window for faster response

        print("VAD: Loaded + smoothing + noise calibration enabled")

    def is_speech(self, frame_bytes, strict=False, tts_energy=0.0):
        """
        strict=True used during SPEAKING (interrupt detection)
        strict=False used during LISTENING
        tts_energy = RMS of TTS output for echo suppression
        """
        if not frame_bytes:
            return False

        audio = np.frombuffer(frame_bytes, dtype=np.int16).astype(np.float32)
        if len(audio) == 0:
            return False

        float_audio = audio / 32768.0
        tensor = torch.tensor(float_audio).unsqueeze(0)

        try:
            prob = float(self.model(tensor, self.sample_rate).item())
        except Exception:
            return False

        # Noise calibration
        if not self.noise_learned:
            self.noise_probs.append(prob)
            if len(self.noise_probs) >= self.noise_frames_needed:
                noise_level = np.mean(self.noise_probs)
                self.dynamic_threshold = max(
                    self.base_threshold, noise_level + 0.20
                )
                self.noise_learned = True
                print(f"VAD: Noise learned → baseline={noise_level:.2f} threshold={self.dynamic_threshold:.2f}")

        # Smoothing
        self.smooth_window.append(prob)
        smooth_prob = float(np.mean(self.smooth_window))

        # Echo suppression – if TTS is loud, raise threshold
        echo_guard = 0.0
        if tts_energy > 500:
            echo_guard = min(0.35, tts_energy / 5000.0)

        threshold = self.dynamic_threshold + echo_guard

        # STRICT: very confident speech, used to detect interrupts
        if strict:
            return smooth_prob > (threshold + 0.10)

        # RELAXED: normal listening with energy fallback
        energy = float(np.sqrt(np.mean(float_audio ** 2)))

        if smooth_prob > threshold:
            return True
        if energy > 0.0008 and smooth_prob > 0.08:  # Lowered thresholds for better sensitivity
            return True

        return False
