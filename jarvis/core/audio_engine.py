import threading
import time
import queue
import random
import numpy as np

from core.state_machine import StateMachine
from core.voice.mic import Microphone
from core.voice.vad import VoiceActivityDetector
from core.voice.stt import SpeechToTextEngine
from core.voice.tts import TextToSpeechEngine
from core.router import Router
from core.voice.aec import AcousticEchoCanceller


class AudioEngine:

    def __init__(self):
        self.state_machine = StateMachine()
        self.mic = Microphone()
        self.vad = VoiceActivityDetector()
        self.stt = SpeechToTextEngine()
        self.aec = AcousticEchoCanceller()

        self.tts = TextToSpeechEngine(on_audio_chunk=self._on_tts_chunk)
        self.router = Router()

        self.is_running = False

        # =============================
        # UTTERANCE CONTROL
        # =============================
        self.silence_frames = 0
        self.MAX_SILENCE_FRAMES = 15      # ~0.5 sec
        self.RMS_THRESHOLD = 900          # adjust for room

        # =============================
        # AEC / TTS REFERENCE
        # =============================
        self.ref_queue = queue.Queue()
        self.tts_energy = 0.0

        # =============================
        # INTERRUPT CONTROL
        # =============================
        self.speech_start_time = None
        self.MIN_BARGEIN_TIME = 0.4
        self.interrupt_frames = 0
        self.INTERRUPT_MIN_FRAMES = 3
        self.ECHO_SUPPRESSION_FACTOR = 2.5

        self.on_text_update = None

    # =====================================================================
    # UTILITY FUNCTIONS
    # =====================================================================

    def _on_tts_chunk(self, chunk):
        """Receive TTS audio chunk and store for AEC."""
        try:
            self.ref_queue.put_nowait(chunk)
        except queue.Full:
            pass

        self.tts_energy = self._calculate_rms(chunk)

    def _calculate_rms(self, chunk) -> float:
        try:
            data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
            if data.size == 0:
                return 0.0
            return float(np.sqrt(np.mean(data**2)))
        except:
            return 0.0

    # =====================================================================
    # PUBLIC START/STOP
    # =====================================================================

    def start(self):
        self.is_running = True
        self.mic.start()
        self.state_machine.set_state("LISTENING")

        greetings = [
            "Jarvis is online. How can I help you, sir?",
            "Systems initialized. I am ready to assist.",
            "Online and ready. What is your command?",
            "Good to see you again. How may I be of service?",
            "Jarvis at your service. All systems nominal.",
        ]
        greeting = random.choice(greetings)
        print("AudioEngine greeting:", greeting)
        self.tts.start_tts_stream(greeting)

        threading.Thread(target=self._main_loop, daemon=True).start()
        print("AudioEngine started.")

    def stop(self):
        self.is_running = False
        self.mic.stop()
        self.tts.stop_tts_stream()

    # =====================================================================
    # MAIN LOOP
    # =====================================================================

    def _main_loop(self):
        print("AudioEngine: Main loop started")
        while self.is_running:
            try:
                state = self.state_machine.get_state()

                # ----------------------------------------------------------
                # SLEEP MODE
                # ----------------------------------------------------------
                if state == "SLEEP":
                    chunk = self.mic.read_chunk()
                    if chunk:
                        rms = self._calculate_rms(chunk)

                        if rms > self.RMS_THRESHOLD:
                            if self.vad.is_speech(chunk):
                                self.stt.buffer_frame(chunk)
                                self.silence_frames = 0
                            else:
                                if self.stt.buffer:
                                    self.silence_frames += 1
                                    self.stt.buffer_frame(chunk)
                                    if self.silence_frames > self.MAX_SILENCE_FRAMES:
                                        text = self.stt.transcribe_buffer()
                                        self.stt.clear_buffer()
                                        if text:
                                            tl = text.lower()
                                            if (
                                                "wake up" in tl or
                                                "hey jarvis" in tl or
                                                "jarvis" in tl
                                            ):
                                                self.state_machine.set_state("LISTENING")
                                                self.tts.start_tts_stream(
                                                    "I am awake and listening, sir."
                                                )
                                        self.silence_frames = 0

                    time.sleep(0.01)
                    continue

                # ----------------------------------------------------------
                # SPEAKING MODE  (complete rewritten block)
                # ----------------------------------------------------------
                if state == "SPEAKING":

                    # TTS finished?
                    if not self.tts.is_speaking():
                        print("AudioEngine: TTS finished → LISTENING")
                        self.state_machine.set_state("LISTENING")
                        self.tts_energy = 0.0
                        self.speech_start_time = None
                        self.interrupt_frames = 0

                        while not self.ref_queue.empty():
                            try:
                                self.ref_queue.get_nowait()
                            except:
                                break

                        time.sleep(0.01)
                        continue

                    # no interrupts during first 400ms
                    if self.speech_start_time and (
                        time.time() - self.speech_start_time < self.MIN_BARGEIN_TIME
                    ):
                        time.sleep(0.01)
                        continue

                    # read mic
                    mic_chunk = self.mic.read_chunk()
                    if not mic_chunk:
                        time.sleep(0.005)
                        continue

                    # get latest TTS frame for AEC
                    ref_chunk = None
                    max_ref_energy = 0.0

                    while not self.ref_queue.empty():
                        try:
                            ch = self.ref_queue.get_nowait()
                            ref_chunk = ch
                            e = self._calculate_rms(ch)
                            if e > max_ref_energy:
                                max_ref_energy = e
                        except:
                            break

                    if max_ref_energy > 0:
                        self.tts_energy = max_ref_energy

                    # AEC clean
                    if ref_chunk:
                        clean_chunk = self.aec.process(mic_chunk, ref_chunk)
                    else:
                        clean_chunk = mic_chunk

                    clean_rms = self._calculate_rms(clean_chunk)

                    # ----------------- TRUE SIRI INTERRUPTION ------------------

                    interrupt_gate = max(
                        self.RMS_THRESHOLD * 0.7,
                        self.tts_energy * 1.15
                    )

                    vad_speech = self.vad.is_speech(
                        clean_chunk,
                        strict=True,
                        tts_energy=self.tts_energy
                    )

                    if vad_speech and clean_rms > interrupt_gate:
                        self.interrupt_frames += 1
                    else:
                        self.interrupt_frames = 0

                    if self.interrupt_frames >= 3:
                        print("AudioEngine: USER INTERRUPTED (REAL SPEECH)")
                        self.tts.stop_tts_stream()
                        self.stt.clear_buffer()
                        self.stt.buffer_frame(clean_chunk)
                        self.silence_frames = 0
                        self.interrupt_frames = 0
                        self.state_machine.set_state("LISTENING")
                        continue

                    time.sleep(0.005)
                    continue

                # ----------------------------------------------------------
                # LISTENING MODE
                # ----------------------------------------------------------
                if state == "LISTENING":

                    chunk = self.mic.read_chunk()
                    if not chunk:
                        time.sleep(0.001)
                        continue

                    rms = self._calculate_rms(chunk)
                    threshold = (
                        self.RMS_THRESHOLD * 0.6
                        if self.stt.buffer
                        else self.RMS_THRESHOLD
                    )

                    # amplitude gate
                    if rms <= threshold:
                        is_speaking = False
                    else:
                        is_speaking = self.vad.is_speech(chunk)

                    # user is speaking
                    if is_speaking:
                        self.stt.buffer_frame(chunk)
                        self.silence_frames = 0

                    else:
                        # trailing silence detection
                        if self.stt.buffer:
                            self.silence_frames += 1
                            self.stt.buffer_frame(chunk)

                            if self.silence_frames > self.MAX_SILENCE_FRAMES:
                                print("AudioEngine: end-of-speech → THINKING")

                                self.state_machine.set_state("THINKING")
                                text = self.stt.transcribe_buffer()
                                self.stt.clear_buffer()
                                self.silence_frames = 0

                                if text and len(text) > 2:
                                    print("User:", text)
                                    if self.on_text_update:
                                        try:
                                            self.on_text_update("user", text)
                                        except Exception as e:
                                            print(f"AudioEngine: GUI update failed: {e}")
                                            self.on_text_update = None

                                    response = self.router.route(text)
                                    action = response.get("action")
                                    reply = response.get("text") or response.get("reply")

                                    if action in ("go_to_sleep", "enable_sleep_mode"):
                                        self.state_machine.set_state("SLEEP")
                                        self.tts.start_tts_stream(
                                            "Going to sleep. Say wake up to reactivate me."
                                        )
                                        continue

                                    if reply:
                                        self.state_machine.set_state("SPEAKING")
                                        self.speech_start_time = time.time()
                                        if self.on_text_update:
                                            try:
                                                self.on_text_update("jarvis", reply)
                                            except Exception as e:
                                                print(f"AudioEngine: GUI update failed: {e}")
                                                self.on_text_update = None
                                        self.tts.start_tts_stream(reply)
                                    else:
                                        self.state_machine.set_state("LISTENING")

                                else:
                                    self.state_machine.set_state("LISTENING")

                # ----------------------------------------------------------
                # THINKING MODE
                # ----------------------------------------------------------
                elif state == "THINKING":
                    chunk = self.mic.read_chunk()
                    if chunk and self.vad.is_speech(chunk):
                        self.stt.clear_buffer()
                        self.stt.buffer_frame(chunk)
                        self.state_machine.set_state("LISTENING")
                        self.silence_frames = 0

                    time.sleep(0.01)

                # ----------------------------------------------------------
                # IDLE MODE
                # ----------------------------------------------------------
                elif state == "IDLE":
                    time.sleep(0.1)
                    self.state_machine.set_state("LISTENING")
                    if not self.mic.stream or not self.mic.stream.is_active():
                        self.mic.start()

                time.sleep(0.001)

            except Exception as e:
                print("AudioEngine ERROR:", e)
                import traceback
                traceback.print_exc()
                time.sleep(1)
