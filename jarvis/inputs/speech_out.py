"""
SpeechOut - Voice output for Jarvis
Uses Edge TTS for natural neural voice with pyttsx3 fallback.
"""
import threading
import queue
import time

# Try to import Edge TTS engine first
try:
    from core.voice.edge_tts_engine import EdgeTTSEngine, EDGE_TTS_AVAILABLE
except ImportError:
    try:
        from jarvis.core.voice.edge_tts_engine import EdgeTTSEngine, EDGE_TTS_AVAILABLE
    except ImportError:
        EDGE_TTS_AVAILABLE = False
        EdgeTTSEngine = None


class SpeechOut:
    """
    Voice output handler with neural TTS for natural speech.
    Falls back to pyttsx3 if Edge TTS unavailable.
    """
    
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.interrupt = False
        self.worker_thread = None
        self.last_spoken = None
        self.last_spoken_time = 0
        
        # Try to use Edge TTS (much better quality)
        self.use_edge_tts = EDGE_TTS_AVAILABLE
        self.edge_engine = None
        
        if self.use_edge_tts:
            try:
                self.edge_engine = EdgeTTSEngine(voice="guy")
                print("SpeechOut: Using Edge TTS (neural voice)")
            except Exception as e:
                print(f"SpeechOut: Edge TTS failed ({e}), falling back to pyttsx3")
                self.use_edge_tts = False
        
        if not self.use_edge_tts:
            # Fallback: Start pyttsx3 worker thread
            self.worker_thread = threading.Thread(target=self._pyttsx3_worker, daemon=True)
            self.worker_thread.start()
            print("SpeechOut: Using pyttsx3 (SAPI5)")
    
    def _pyttsx3_worker(self):
        """Fallback worker using pyttsx3 (legacy)."""
        import pyttsx3
        import pythoncom
        
        try:
            pythoncom.CoInitialize()
            
            while True:
                try:
                    item = self.speech_queue.get(timeout=1)
                    if item is None:
                        break
                    
                    text, callback = item
                    if not text:
                        if callback:
                            callback()
                        continue
                    
                    self.is_speaking = True
                    self.interrupt = False
                    self.last_spoken = text
                    self.last_spoken_time = time.time()
                    
                    print(f"Jarvis (Voice): {text}")
                    
                    # Initialize engine fresh each time
                    engine = pyttsx3.init(driverName='sapi5')
                    engine.setProperty('rate', 160)  # Slower, warmer
                    engine.setProperty('volume', 0.95)
                    
                    # Select voice - prefer Zira (female, smoother) or David
                    voices = engine.getProperty('voices')
                    for voice in voices:
                        # Try Zira first (smoother), then David
                        if "zira" in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
                        elif "david" in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                    
                    engine.say(text)
                    engine.runAndWait()
                    del engine
                    
                    if not self.interrupt and callback:
                        callback()
                    
                    self.is_speaking = False
                    self.speech_queue.task_done()
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"SpeechOut Error: {e}")
                    self.is_speaking = False
            
            pythoncom.CoUninitialize()
            
        except Exception as e:
            print(f"SpeechOut Worker Fatal Error: {e}")
    
    def speak(self, text, on_complete=None):
        """
        Speak text using neural TTS.
        
        Args:
            text: Text to speak
            on_complete: Optional callback when speech completes
        """
        if not text or not text.strip():
            if on_complete:
                on_complete()
            return
        
        # Track for anti-repetition
        self.last_spoken = text
        self.last_spoken_time = time.time()
        
        print(f"Jarvis (Voice): {text}")
        
        if self.use_edge_tts and self.edge_engine:
            # Use Edge TTS (async, non-blocking)
            self.edge_engine.speak(text)
            # Call completion callback after a delay (estimated)
            if on_complete:
                # Estimate ~100ms per word
                word_count = len(text.split())
                delay = max(0.5, word_count * 0.1)
                threading.Timer(delay, on_complete).start()
        else:
            # Fallback to pyttsx3 queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except queue.Empty:
                    break
            
            self.speech_queue.put((text, on_complete))
    
    def stop(self):
        """Stop current speech immediately."""
        print("SpeechOut: Stopping...")
        self.interrupt = True
        
        if self.use_edge_tts and self.edge_engine:
            self.edge_engine.stop()
        else:
            # Clear pyttsx3 queue
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except queue.Empty:
                    break
    
    def is_busy(self) -> bool:
        """Check if currently speaking."""
        if self.use_edge_tts and self.edge_engine:
            return self.edge_engine.is_speaking()
        return self.is_speaking or not self.speech_queue.empty()
    
    def shutdown(self):
        """Shutdown speech output."""
        if self.use_edge_tts and self.edge_engine:
            self.edge_engine.stop()
        else:
            self.speech_queue.put(None)
            if self.worker_thread:
                self.worker_thread.join(timeout=2)
