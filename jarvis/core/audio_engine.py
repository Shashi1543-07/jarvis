import threading
import time
import queue
import random
import numpy as np

from .voice.state_machine_enhanced import RaceConditionSafeVoiceController, VoiceState
from .voice.mic import Microphone
from .voice.vad import VoiceActivityDetector
from .voice.stt import SpeechToTextEngine
from .voice.tts import TextToSpeechEngine
from .router import Router
from .voice.aec_enhanced import EnhancedAECWithNR
from .voice.wake_word import MultiKeywordWakeWordDetector
from .voice.speaker_id import SpeakerAuthenticator
from .voice.noise_suppression import AdaptiveNoiseSuppressor


class AudioEngine:

    def __init__(self, router=None):
        print("AudioEngine: Initializing...")
        # Enhanced state machine with race condition handling
        self.state_controller = RaceConditionSafeVoiceController()
        self.state_machine = self.state_controller.state_machine
        print("AudioEngine: State Machine ready.")

        # Audio I/O
        self.mic = Microphone()
        print("AudioEngine: Microphone object created.")
        self.vad = VoiceActivityDetector()
        print("AudioEngine: VAD ready.")

        # Enhanced audio processing components
        self.aec = EnhancedAECWithNR()  # Enhanced AEC with noise reduction and double-talk detection
        print("AudioEngine: AEC ready.")
        self.wake_word_detector = MultiKeywordWakeWordDetector()  # Advanced wake word detection
        print("AudioEngine: Wake Word Detector ready.")
        self.speaker_auth = SpeakerAuthenticator()  # Speaker identification and authentication
        print("AudioEngine: Speaker Auth ready.")
        self.noise_suppressor = AdaptiveNoiseSuppressor()  # Adaptive noise suppression
        print("AudioEngine: Noise Suppressor ready.")

        # Core processing engines
        self.stt = SpeechToTextEngine()
        print("AudioEngine: STT ready.")
        self.tts = TextToSpeechEngine(on_audio_chunk=self._on_tts_chunk)
        print("AudioEngine: TTS ready.")

        if router:
            self.router = router
            print("AudioEngine: Using provided Router.")
        else:
            self.router = Router()
            print("AudioEngine: Created new Router.")
        
        # Connect router callbacks to GUI
        self.router.on_intent_classified = self._on_intent_from_router
        
        print("AudioEngine: Router ready.")

        # Async Processing
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.current_request_id = 0

        self.thinking_thread = threading.Thread(target=self._thinking_worker, daemon=True)
        self.thinking_thread.start()

        self.is_running = False

        # ENHANCED UTTERANCE CONTROL
        # Core Logic Parameters
        self.SAFE_MODE = True # Set to True to bypass advanced processing for stability
        self.RMS_THRESHOLD = 30 # Lowered to extreme sensitivity (was 150)
        self.MIN_SPEECH_FRAMES = 1 # Instant capture
        self.MAX_SILENCE_FRAMES = 35 
        self.silence_frames = 0
        self.speech_frames = 0
        self.last_diagnostic_time = 0.0 # Throttled logging

        # Enhanced speaker verification
        self.last_verified_speaker = None
        self.verification_cooldown = 5.0  # seconds between verifications
        self.last_verification_time = 0.0

        # =============================
        # ENHANCED AEC / TTS REFERENCE
        # =============================
        # Enhanced audio processing buffers
        self.ref_byte_buffer = b""  # Byte buffer to handle chunk size mismatches
        self.noise_suppressed_buffer = queue.Queue(maxsize=10)

        # =============================
        # ENHANCED INTERRUPT CONTROL
        # =============================
        self.speech_start_time = None
        self.MIN_BARGEIN_TIME = 0.4
        self.interrupt_frames = 0
        self.INTERRUPT_MIN_FRAMES = 3
        self.ECHO_SUPPRESSION_FACTOR = 2.5

        # Enhanced interruption with speaker verification - made more permissive by default
        self.allow_interruption_by_unknown = True  # Allow interruptions from any speaker initially
        # This can be set to False after enrolling authorized speakers

        self.on_text_update = None
        self.on_audio_level = None
        self.on_latency_update = None
        self.on_intent_detected = None
        
        # Latency tracking
        self.request_start_time = None
        self.last_intent = None

    # =====================================================================
    # ENHANCED UTILITY FUNCTIONS
    # =====================================================================

    def _on_tts_chunk(self, chunk):
        """Receive TTS audio chunk and store in byte buffer for AEC."""
        self.ref_byte_buffer += chunk
        # Keep buffer size reasonable (e.g., max 1 second of audio)
        if len(self.ref_byte_buffer) > 32000:
            self.ref_byte_buffer = self.ref_byte_buffer[-32000:]
        
        self.tts_energy = self._calculate_rms(chunk)

    def _calculate_rms(self, chunk) -> float:
        try:
            data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
            if data.size == 0:
                return 0.0
            return float(np.sqrt(np.mean(data**2)))
        except:
            return 0.0

    def _verify_speaker(self, audio_chunk):
        """Verify speaker identity from audio chunk"""
        try:
            # Convert audio to numpy array for processing
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
            audio_data = audio_data / 32768.0  # Normalize

            # Perform speaker verification
            is_auth, speaker_id, confidence = self.speaker_auth.authenticate(audio_data)

            if is_auth and speaker_id:
                self.last_verified_speaker = speaker_id
                self.last_verification_time = time.time()
                return True, speaker_id, confidence
            else:
                return False, None, 0.0
        except Exception as e:
            print(f"Speaker verification error: {e}")
            return False, None, 0.0

    def _apply_noise_suppression(self, audio_chunk):
        """Apply noise suppression to audio chunk"""
        try:
            # Process with adaptive noise suppressor
            suppressed_chunk, _ = self.noise_suppressor.process_frame(audio_chunk)
            return suppressed_chunk
        except Exception as e:
            print(f"Noise suppression error: {e}")
            return audio_chunk  # Return original if processing fails

    def _on_intent_from_router(self, intent_name, confidence):
        """Forward intent classification from router to GUI"""
        if self.on_intent_detected:
            try:
                self.on_intent_detected(intent_name, confidence)
            except Exception as e:
                print(f"AudioEngine: Failed to forward intent to GUI: {e}")

    def _thinking_worker(self):
        """Worker thread for router logic"""
        print("AudioEngine: Thinking worker started")
        while True:
            try:
                item = self.request_queue.get()
                if item is None: # Sentinel
                    break

                req_id, text = item

                try:
                    response = self.router.route(text)
                    self.response_queue.put((req_id, {"type": "response", "data": response}))
                except Exception as e:
                    print(f"AudioEngine: Error in background thinking: {e}")
                    self.response_queue.put((req_id, {"type": "error", "error": str(e)}))

                self.request_queue.task_done()
            except Exception as e:
                print(f"AudioEngine: Thinking worker error: {e}")

    def _process_thinking_result(self, req_id, result):
        """Process the result from the background thread in the main loop"""
        if req_id != self.current_request_id:
            print(f"AudioEngine: Ignoring stale result (ID: {req_id} != {self.current_request_id})")
            return

        if result.get("type") == "error":
            print(f"AudioEngine: Error processing request: {result.get('error')}")
            self.state_controller.safe_state_transition(VoiceState.LISTENING)
            return

        response = result.get("data")
        action = response.get("action")
        reply = response.get("text") or response.get("reply")

        if action in ("go_to_sleep", "enable_sleep_mode"):
            self.state_controller.safe_state_transition(VoiceState.SLEEP)
            self.tts.start_tts_stream(
                "Going to sleep. Say wake up to reactivate me."
            )
            return

        if reply:
            self.state_controller.safe_state_transition(VoiceState.SPEAKING)
            self.speech_start_time = time.time()

            # Calculate and emit latency
            if self.request_start_time:
                latency_ms = int((time.time() - self.request_start_time) * 1000)
                print(f"AudioEngine: Response latency: {latency_ms}ms")
                if self.on_latency_update:
                    try:
                        self.on_latency_update(latency_ms)
                    except Exception as e:
                        print(f"AudioEngine: GUI latency update failed: {e}")
                self.request_start_time = None

            if self.on_text_update:
                try:
                    self.on_text_update("jarvis", reply)
                except Exception as e:
                    print(f"AudioEngine: GUI chat update failed: {e}")
            self.tts.start_tts_stream(reply)
        else:
            print("AudioEngine: Empty response (filler handled) → LISTENING")
            self.state_controller.safe_state_transition(VoiceState.LISTENING)

    # =====================================================================
    # PUBLIC START/STOP
    # =====================================================================

    def start(self):
        self.is_running = True
        print("AudioEngine: Starting mic...")
        self.mic.start()

        # Initialize in IDLE first, then transition to LISTENING
        print("AudioEngine: Initializing state...")
        self.state_controller.safe_state_transition(VoiceState.IDLE)
        time.sleep(0.1)  # Brief pause to ensure state is set
        self.state_controller.safe_state_transition(VoiceState.LISTENING)
        print(f"AudioEngine: State set to {self.state_machine.get_state().value}")

        greetings = [
            "Jarvis is online. How can I help you, sir?",
            "Systems initialized. I am ready to assist.",
            "Online and ready. What is your command?",
            "Good to see you again. How may I be of service?",
            "Jarvis at your service. All systems nominal.",
        ]
        greeting = random.choice(greetings)
        # Transition to SPEAKING during greeting to avoid self-triggering
        self.state_controller.safe_state_transition(VoiceState.SPEAKING)
        print("AudioEngine: Playing greeting...")
        self.tts.start_tts_stream(greeting)
        time.sleep(0.5) # Let tts initialize so is_speaking() becomes True

        # Force transition to LISTENING after a short delay or after TTS finishes
        # The main_loop will also handle the return to LISTENING once tts.is_speaking() is False

        # Start the processing loop
        threading.Thread(target=self._main_loop, daemon=True).start()
        print("AudioEngine started with enhanced features.")

        # Ensure microphone is active
        if not self.mic.stream or not self.mic.stream.is_active():
            self.mic.start()

    def stop(self):
        self.is_running = False
        self.mic.stop()
        self.tts.stop_tts_stream()
        # self.thinking_thread is daemon, will die with process
        # But we can try to be nice
        self.request_queue.put(None)

    # =====================================================================
    # ENHANCED MAIN LOOP
    # =====================================================================

    def _main_loop(self):
        print("AudioEngine: Enhanced main loop started")
        last_log_time = time.time()
        while self.is_running:
            try:
                state = self.state_machine.get_state()
                
                # State processing

                # ----------------------------------------------------------
                # SLEEP MODE - Enhanced with wake word detection
                # ----------------------------------------------------------
                if state == VoiceState.SLEEP:
                    chunk = self.mic.read_chunk()
                    if chunk:
                        # Even in sleep mode, always listen for wake words
                        # Apply noise suppression first
                        processed_chunk = self._apply_noise_suppression(chunk)

                        # Check for wake word using enhanced detector
                        is_wake_word, confidence = self.wake_word_detector.detect_wake_word(processed_chunk)

                        if is_wake_word:
                            # Verify speaker if authentication is enabled
                            is_auth, speaker_id, auth_confidence = self._verify_speaker(processed_chunk)

                            if is_auth or not self.speaker_auth.is_access_control_enabled():
                                # Wake up the system
                                self.state_controller.safe_state_transition(VoiceState.WAKE_WORD_DETECTED)
                                self.tts.start_tts_stream(
                                    f"Hello {speaker_id or 'user'}, I am awake and listening."
                                )
                            else:
                                # Unauthorized speaker
                                print(f"Unauthorized wake word detected from unknown speaker")
                        else:
                            # Also check for traditional wake phrases as fallback
                            rms = self._calculate_rms(processed_chunk)
                            if rms > self.RMS_THRESHOLD * 0.3:  # Lower threshold in sleep mode
                                # Check if it's speech-like
                                if self.vad.is_speech(processed_chunk):
                                    # Convert to text to check for wake phrases
                                    # For now, just buffer and check for keywords
                                    temp_buffer = [processed_chunk]
                                    # This is a simplified check - in practice, you'd need a quick keyword spotter
                                    # But for now, we'll rely on the enhanced wake word detector above
                                    pass

                    time.sleep(0.01)
                    continue

                # ----------------------------------------------------------
                # SPEAKING MODE - Enhanced with advanced interruption handling
                # ----------------------------------------------------------
                if state == VoiceState.SPEAKING:
                    # TTS finished?
                    if not self.tts.is_speaking():
                        # If speaker stopped, we return to LISTENING immediately
                        # and clear any stale reference audio
                        print("AudioEngine: TTS finished (Speaker Idle) → LISTENING")
                        self.state_controller.safe_state_transition(VoiceState.LISTENING)
                        self.ref_byte_buffer = b"" 
                        self.tts_energy = 0.0
                        self.speech_start_time = None
                        self.interrupt_frames = 0
                        time.sleep(0.01)
                        continue

                    # read mic
                    mic_chunk = self.mic.read_chunk()
                    if not mic_chunk:
                        time.sleep(0.005)
                        continue

                    # get exactly 1024 bytes (512 samples) from ref_byte_buffer for AEC
                    target_bytes = 1024 
                    ref_chunk = None
                    
                    if len(self.ref_byte_buffer) >= target_bytes:
                        ref_chunk = self.ref_byte_buffer[:target_bytes]
                        self.ref_byte_buffer = self.ref_byte_buffer[target_bytes:]
                        self.tts_energy = self._calculate_rms(ref_chunk)
                    else:
                        self.tts_energy = 0.0

                    # Enhanced AEC with double-talk detection
                    if ref_chunk and not self.SAFE_MODE:
                        clean_chunk, echo_reduction_db = self.aec.process_with_noise_reduction(mic_chunk, ref_chunk)
                    else:
                        clean_chunk = mic_chunk

                    clean_rms = self._calculate_rms(clean_chunk)

                    # ----------------- ENHANCED SIRI-LIKE INTERRUPTION ------------------
                    # Check if interruption should be allowed based on speaker verification
                    is_auth_speaker = False
                    if time.time() - self.last_verification_time > self.verification_cooldown:
                        is_auth, speaker_id, conf = self._verify_speaker(clean_chunk)
                        is_auth_speaker = is_auth

                    # Determine if interruption should be allowed
                    interrupt_allowed = (
                        is_auth_speaker or
                        not self.speaker_auth.is_access_control_enabled() or
                        self.allow_interruption_by_unknown
                    )

                    interrupt_gate = max(
                        self.RMS_THRESHOLD * 0.7,
                        self.tts_energy * 1.15
                    )

                    vad_speech = self.vad.is_speech(
                        clean_chunk,
                        strict=True,
                        tts_energy=self.tts_energy
                    )

                    if vad_speech and clean_rms > interrupt_gate and interrupt_allowed:
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
                        self.state_controller.safe_state_transition(VoiceState.LISTENING)
                        continue

                    time.sleep(0.005)
                    continue

                # ----------------------------------------------------------
                # LISTENING MODE - Enhanced with noise suppression and speaker verification
                # ----------------------------------------------------------
                if state == VoiceState.LISTENING:

                    chunk = self.mic.read_chunk()
                    if not chunk:
                        time.sleep(0.001)
                        continue

                    # Apply noise suppression
                    if self.SAFE_MODE:
                        processed_chunk = chunk
                    else:
                        processed_chunk = self._apply_noise_suppression(chunk)

                    rms = self._calculate_rms(processed_chunk)
                    # Lower threshold for better sensitivity
                    threshold = (
                        self.RMS_THRESHOLD * 0.3  # Stay (45) - lowered from 0.4
                        if self.stt.buffer
                        else self.RMS_THRESHOLD * 0.5  # Start (75) - lowered from 0.6
                    )

                    # amplitude gate
                    if rms <= threshold:
                        is_speaking = False
                    else:
                        # Use VAD with lower sensitivity for better detection
                        is_speaking = self.vad.is_speech(processed_chunk)

                    # Diagnostic logging once every 2 seconds
                    if time.time() - self.last_diagnostic_time > 2.0:
                        vad_status = "SPEECH" if is_speaking else "SILENCE"
                        print(f"[LISTENING] RMS: {rms:.1f} (Threshold: {threshold:.1f}) VAD: {vad_status}")
                        self.last_diagnostic_time = time.time()

                    # Emit audio level to GUI if subscribed
                    if self.on_audio_level:
                        # Normalize RMS for HUD (0-100 range roughly)
                        # self.RMS_THRESHOLD is 30, so let's scale accordingly
                        scaled_level = min(100, (rms / 300.0) * 100)
                        self.on_audio_level(scaled_level)

                    # user is speaking
                    if is_speaking:
                        self.speech_frames += 1
                        if self.speech_frames >= self.MIN_SPEECH_FRAMES or self.stt.buffer:
                            self.stt.buffer_frame(processed_chunk)
                            self.silence_frames = 0
                    else:
                        self.speech_frames = 0
                        # trailing silence detection
                        if self.stt.buffer:
                            self.silence_frames += 1
                            self.stt.buffer_frame(processed_chunk)

                            if self.silence_frames > self.MAX_SILENCE_FRAMES:
                                print("AudioEngine: end-of-speech → THINKING")

                                self.state_controller.safe_state_transition(VoiceState.THINKING)
                                text = self.stt.transcribe_buffer()
                                self.stt.clear_buffer()
                                self.silence_frames = 0

                                if text and len(text) > 2:
                                    print("User:", text)
                                    
                                    # Track request start time for latency calculation
                                    self.request_start_time = time.time()
                                    
                                    if self.on_text_update:
                                        try:
                                            self.on_text_update("user", text)
                                        except Exception as e:
                                            print(f"AudioEngine: GUI chat update failed: {e}")
                                            # Don't disable callback, just log the error

                                    # Submit thinking task to worker
                                    self.current_request_id += 1
                                    self.request_queue.put((self.current_request_id, text))

                                else:
                                    self.state_controller.safe_state_transition(VoiceState.LISTENING)
                                    self.speech_frames = 0
                        else:
                            # If no buffer, stay in listening but reset silence counter
                            self.silence_frames = 0
                            self.speech_frames = 0

                # ----------------------------------------------------------
                # THINKING MODE - Enhanced with speaker verification during processing
                # ----------------------------------------------------------
                elif state == VoiceState.THINKING:
                    # Check for results
                    try:
                        req_id, result = self.response_queue.get_nowait()
                        self._process_thinking_result(req_id, result)
                        continue
                    except queue.Empty:
                        pass

                    chunk = self.mic.read_chunk()
                    if chunk and self.vad.is_speech(chunk):
                        # Verify speaker during thinking mode to allow interruption
                        is_auth, speaker_id, conf = self._verify_speaker(chunk)

                        interrupt_allowed = (
                            is_auth or
                            not self.speaker_auth.is_access_control_enabled() or
                            self.allow_interruption_by_unknown
                        )

                        if interrupt_allowed:
                            print("AudioEngine: User interrupted thinking...")
                            self.stt.clear_buffer()
                            self.stt.buffer_frame(chunk)
                            # Note: The background thread will still complete, but we will ignore its result
                            # because we transitioned state.
                            # We might need to drain queue later or check request ID, but for now state check is enough?
                            # _process_thinking_result is called in this loop only if state is THINKING.
                            # If we change state here, the next loop won't call it.
                            self.state_controller.safe_state_transition(VoiceState.LISTENING)
                            self.silence_frames = 0

                    time.sleep(0.01)

                # ----------------------------------------------------------
                # IDLE MODE
                # ----------------------------------------------------------
                elif state == VoiceState.IDLE:
                    time.sleep(0.1)
                    self.state_controller.safe_state_transition(VoiceState.LISTENING)
                    if not self.mic.stream or not self.mic.stream.is_active():
                        self.mic.start()

                time.sleep(0.001)

            except Exception as e:
                print("AudioEngine ERROR:", e)
                import traceback
                traceback.print_exc()
                time.sleep(1)
