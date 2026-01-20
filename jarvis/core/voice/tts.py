import threading
import queue
import pyttsx3
import pythoncom
import pyaudio
import wave
import tempfile
import os

class TextToSpeechEngine:
    """
    File-based TTS with PyAudio for stream access and interruption.
    Generates audio file, plays with PyAudio, sends chunks to callback.
    """
    def __init__(self, on_audio_chunk=None):
        self.speech_queue = queue.Queue()
        self.is_playing = False
        self.stop_event = threading.Event()
        self.temp_file = None
        self.on_audio_chunk = on_audio_chunk # Callback for AEC
        
        # PyAudio initialization
        self.p = pyaudio.PyAudio()
        
        # Start worker thread
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        print("TTS: Using PyAudio for playback with stream access")

    def start_tts_stream(self, text):
        """Queue text to be spoken"""
        # Clear any pending speech
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        
        self.stop_event.clear()
        self.speech_queue.put(text)

    def stop_tts_stream(self):
        """Stop current speech IMMEDIATELY"""
        self.stop_event.set()
        self.is_playing = False
        print("TTS: Stopped immediately")

    def is_speaking(self):
        return self.is_playing or not self.speech_queue.empty()

    def _worker(self):
        """Worker thread that processes speech queue"""
        pythoncom.CoInitialize()
        
        while True:
            try:
                text = self.speech_queue.get(timeout=1)
                if text is None:
                    break
                
                self.is_playing = True
                self.stop_event.clear()
                
                # Generate audio file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    self.temp_file = f.name
                
                # Use pyttsx3 to save to file
                engine = pyttsx3.init(driverName='sapi5')
                engine.setProperty('rate', 175)
                engine.setProperty('volume', 1.0)
                
                # Select voice
                voices = engine.getProperty('voices')
                for voice in voices:
                    if "david" in voice.name.lower() or "male" in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                
                # Save to file
                engine.save_to_file(text, self.temp_file)
                engine.runAndWait()
                
                # Debug: Check file size
                if os.path.exists(self.temp_file):
                    size = os.path.getsize(self.temp_file)
                    print(f"TTS: Generated WAV size: {size} bytes")
                else:
                    print("TTS: FAILED to generate WAV file")
                
                del engine
                
                # Check interruption
                if self.stop_event.is_set():
                    self._cleanup_temp_file()
                    self.is_playing = False
                    continue
                
                # Play with PyAudio
                try:
                    wf = wave.open(self.temp_file, 'rb')
                    stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
                                       channels=wf.getnchannels(),
                                       rate=wf.getframerate(),
                                       output=True)
                    
                    chunk_size = 1024
                    data = wf.readframes(chunk_size)
                    
                    if not data:
                        print("TTS: WAV file is EMPTY")
                    else:
                        print(f"TTS: Playing audio... ({wf.getnchannels()} channels, {wf.getframerate()}Hz)")
                    
                    while data:
                        if self.stop_event.is_set():
                            break
                            
                        stream.write(data)
                        
                        # Send chunk to AEC callback
                        if self.on_audio_chunk:
                            # Resample to 16000Hz for AEC compatibility
                            try:
                                import numpy as np
                                # Convert bytes to int16
                                audio_data = np.frombuffer(data, dtype=np.int16)
                                
                                # Handle Stereo -> Mono
                                if wf.getnchannels() == 2:
                                    audio_data = audio_data.reshape(-1, 2)
                                    audio_data = audio_data.mean(axis=1).astype(np.int16)
                                
                                # Resample if rate != 16000
                                current_rate = wf.getframerate()
                                if current_rate != 16000:
                                    # Simple linear interpolation
                                    duration = len(audio_data) / current_rate
                                    new_samples = int(duration * 16000)
                                    indices = np.linspace(0, len(audio_data)-1, new_samples)
                                    resampled_data = np.interp(indices, np.arange(len(audio_data)), audio_data).astype(np.int16)
                                    
                                    self.on_audio_chunk(resampled_data.tobytes())
                                else:
                                    self.on_audio_chunk(audio_data.tobytes())
                            except Exception as e:
                                print(f"TTS Resample Error: {e}")
                                self.on_audio_chunk(data)
                            
                        data = wf.readframes(chunk_size)
                    
                    stream.stop_stream()
                    stream.close()
                    wf.close()
                    
                except Exception as e:
                    print(f"TTS Playback Error: {e}")
                
                # Cleanup
                self._cleanup_temp_file()
                self.is_playing = False
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"TTS Worker Error: {e}")
                self.is_playing = False
                self._cleanup_temp_file()
        
        pythoncom.CoUninitialize()
    
    def _cleanup_temp_file(self):
        """Delete temporary audio file"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.unlink(self.temp_file)
            except:
                pass
            self.temp_file = None
    
    def __del__(self):
        self.p.terminate()
