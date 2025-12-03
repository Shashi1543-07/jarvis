import wave
from faster_whisper import WhisperModel
import os
from .audio_preprocessor import AudioPreprocessor


class SpeechToTextEngine:
    def __init__(self, model_size="base.en", device="cpu", compute_type="int8"):
        """
        Initialize Faster Whisper with audio preprocessing.
        device: 'cuda' or 'cpu'
        compute_type: 'float16' or 'int8'
        """
        print(f"Loading Whisper model: {model_size} on {device}...")
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            print("Whisper model loaded.")
        except Exception as e:
            print(f"Error loading Whisper: {e}")
            self.model = None

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
        if duration_sec < 0.35:
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
            segments, info = self.model.transcribe(
                self.temp_filename,
                beam_size=1,             # Faster inference
                language="en",
                condition_on_previous_text=False
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
                beam_size=1,
                language="en",
                condition_on_previous_text=False
            )
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        except Exception as e:
            print(f"STT: Transcription Error - {e}")
            return ""
