import wave
from faster_whisper import WhisperModel
import os
from .audio_preprocessor import AudioPreprocessor


class SpeechToTextEngine:
    def __init__(self, model_size="small.en", device=None, compute_type=None):
        """
        Initialize Faster Whisper with GPU acceleration support.
        Using small.en for better accuracy - downloads ~460MB on first run.
        """
        import torch
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        if compute_type is None:
            compute_type = "float16" if device == "cuda" else "int8"
        
        self.model = None
        self.device = device
        
        print(f"Loading Whisper model: {model_size} on {device} ({compute_type})...")
        
        try:
            # Clear GPU cache before loading to prevent memory issues
            if device == "cuda":
                torch.cuda.empty_cache()
            
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            print(f"Whisper {model_size} loaded successfully on {device}.")
            
        except Exception as e:
            print(f"Error loading Whisper {model_size}: {e}")
            # If CUDA fails, try CPU as fallback
            if device == "cuda":
                print("Trying CPU fallback for Whisper...")
                try:
                    torch.cuda.empty_cache()
                    self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
                    print(f"Whisper {model_size} loaded on CPU (fallback).")
                except Exception as e2:
                    print(f"CPU fallback failed: {e2}")
        
        if self.model is None:
            print("CRITICAL: STT model failed to load!")


        # Audio preprocessing
        self.preprocessor = AudioPreprocessor(target_sample_rate=16000)

        self.buffer = []
        self.temp_filename = "temp_buffer.wav"
        self.sample_rate = 16000

    # ---------------------------------------------------------
    # Buffer management
    # ---------------------------------------------------------

    def buffer_frame(self, frame: bytes):
        """
        Add one audio frame to the buffer, with lightweight preprocessing.
        This also lets the AudioPreprocessor learn the noise profile online.
        """
        processed = self.preprocessor.process_chunk(frame)
        self.buffer.append(processed)

    def clear_buffer(self):
        self.buffer = []

    # ---------------------------------------------------------
    # Main transcription path
    # ---------------------------------------------------------

    def transcribe_buffer(self):
        if not self.buffer:
            return ""

        print("STT: Preprocessing audio...")

        # Heavy preprocessing on the whole utterance
        processed_audio = self.preprocessor.process_complete_audio(self.buffer)

        if processed_audio is None:
            print("STT: Audio quality too low, skipping transcription")
            return ""

        # Minimum duration check (avoid transcribing tiny/noisy chunks)
        total_samples = len(processed_audio) // 2  # int16 => 2 bytes
        duration_sec = total_samples / float(self.sample_rate)
        if duration_sec < 0.2:
            print(f"STT: Utterance too short ({duration_sec:.2f}s), ignoring")
            return ""

        # Save preprocessed audio to WAV
        try:
            with wave.open(self.temp_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(processed_audio)

            print("STT: Running Whisper transcription...")
            # Use better beam size and initial prompt for command recognition
            segments, info = self.model.transcribe(
                self.temp_filename,
                beam_size=5,             # Better accuracy (was 1)
                language="en",
                condition_on_previous_text=False,
                initial_prompt="Hey Jarvis, turn on wifi, turn off bluetooth, enable hotspot, open chrome, set volume, set brightness"  # Bias towards common commands
            )
            text = " ".join([segment.text for segment in segments]).strip()

            print(f"STT: Transcription complete - {len(text)} chars")
            return text
        except Exception as e:
            print(f"STT: Transcription Error - {e}")
            return ""
        finally:
            if os.path.exists(self.temp_filename):
                os.remove(self.temp_filename)

    def transcribe(self, audio_data):
        """
        Transcribe audio data (file path or numpy array).
        """
        if not self.model:
            return ""

        try:
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=5,
                language="en",
                condition_on_previous_text=False,
                initial_prompt="Hey Jarvis, turn on wifi, turn off bluetooth, enable hotspot, open chrome"
            )
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        except Exception as e:
            print(f"STT: Transcription Error - {e}")
            return ""
