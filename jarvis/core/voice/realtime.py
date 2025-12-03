import pyaudio
import numpy as np
import time
import threading
import queue
import wave
import os
from core.voice.vad import VoiceActivityDetector
from core.voice.tts import TextToSpeechEngine
from core.voice.stt import SpeechToTextEngine
from core.router import Router

class RealtimeVoicePipeline:
    def __init__(self):
        self.vad = VoiceActivityDetector(aggressiveness=3)
        self.tts = TextToSpeechEngine()
        self.stt = SpeechToTextEngine()
        self.router = Router()
        
        self.is_running = False
        self.state = "IDLE"
        
        # Audio Config
        self.p = pyaudio.PyAudio()
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 512 # 32ms
        
        # Callbacks
        self.on_state_change = None
        self.on_response = None

    def _set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            print(f"State: {self.state}")
            if self.on_state_change:
                self.on_state_change(new_state)

    def start(self):
        self.is_running = True
        threading.Thread(target=self._main_loop, daemon=True).start()

    def stop(self):
        self.is_running = False
        self.tts.stop()
        self.p.terminate()

    def _main_loop(self):
        print("Voice Pipeline Started.")
        
        while self.is_running:
            # --- STATE: LISTENING ---
            self._set_state("LISTENING")
            frames = self._listen_for_speech()
            
            if not frames:
                continue # Loop back if no speech (or stopped)

            # --- STATE: THINKING ---
            self._set_state("THINKING")
            text = self._transcribe(frames)
            
            if not text:
                continue

            # --- STATE: ACTION / SPEAKING ---
            # Route returns a dict with 'text' (speech) and 'action' details
            response = self.router.route(text)
            
            if self.on_response:
                self.on_response(text, response)
            
            reply_text = response.get("text") or response.get("reply")
            
            if reply_text:
                self._set_state("SPEAKING")
                print(f"Jarvis: {reply_text}")
                self.tts.speak_blocking(reply_text)
            
            # Loop back to LISTENING

    def _listen_for_speech(self):
        """
        Records audio until silence is detected.
        Returns list of frames.
        """
        stream = self.p.open(format=self.FORMAT,
                             channels=self.CHANNELS,
                             rate=self.RATE,
                             input=True,
                             frames_per_buffer=self.CHUNK)
        
        frames = []
        speech_detected = False
        silence_frames = 0
        MAX_SILENCE = 30 # ~1 second of silence to stop
        MIN_SPEECH_FRAMES = 15 # ~0.5s min duration
        
        try:
            while self.is_running:
                # Check if TTS is playing (e.g. triggered by GUI or other thread)
                if self.tts.is_playing:
                    time.sleep(0.1)
                    continue
                    
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                except:
                    continue
                    
                is_speech = self.vad.is_speech(data)
                
                if is_speech:
                    speech_detected = True
                    silence_frames = 0
                    frames.append(data)
                else:
                    if speech_detected:
                        silence_frames += 1
                        frames.append(data) # Keep trailing silence for natural cut
                        if silence_frames > MAX_SILENCE:
                            break # End of speech
                    else:
                        # Buffer some pre-speech silence? Or just ignore.
                        pass
                        
        except Exception as e:
            print(f"Listening Error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            
        if len(frames) < MIN_SPEECH_FRAMES:
            return None
            
        return frames

    def _transcribe(self, frames):
        temp_filename = "temp_voice_input.wav"
        try:
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(frames))
                
            text = self.stt.transcribe(temp_filename)
            text = text.strip()
            
            # Hallucination Filter
            hallucinations = ["you", "thank you", "thanks", "bye", "ok", "okay", "subtitle", "subtitles"]
            if not text or len(text) < 2 or text.lower() in hallucinations:
                return None
                
            print(f"User said: {text}")
            return text
        except Exception as e:
            print(f"Transcription Error: {e}")
            return None
        finally:
            # Cleanup temp file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def _wait_for_tts(self):
        """
        Blocks until TTS finishes playing.
        """
        # Give it a moment to start
        time.sleep(0.1) 
        while self.tts.is_playing and self.is_running:
            time.sleep(0.1)
