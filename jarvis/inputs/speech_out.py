import threading
import queue
import pyttsx3
import pythoncom
import time

class SpeechOut:
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.is_speaking = False
        self.should_stop = threading.Event() # This was the original interrupt mechanism
        self.interrupt = False # New interrupt flag as per instruction
        self.worker_thread = None
        self.completion_callback = None
        self.last_spoken = None
        self.last_spoken_time = 0
        
        # Start the dedicated speech worker thread
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()
        
        print("SpeechOut: Initialized with queue-based threading")

    def _speech_worker(self):
        """Dedicated worker thread that processes speech queue"""
        import datetime
        
        with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
            f.write(f"\n{datetime.datetime.now()}: Worker thread STARTED\n")
        
        try:
            # Initialize COM for Windows SAPI5
            pythoncom.CoInitialize()
            
            with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.datetime.now()}: COM initialized\n")
            
            while True:
                try:
                    # Wait for speech text from queue
                    text, callback = self.speech_queue.get(timeout=1)
                    
                    if text is None:  # Shutdown signal
                        break
                    
                    self.is_speaking = True
                    self.should_stop.clear() # Original interrupt mechanism
                    self.interrupt = False # Reset new interrupt flag for new utterance
                    
                    self.interrupt = False # Reset new interrupt flag for new utterance
                    
                    self.last_spoken = text
                    self.last_spoken_time = time.time()
                    
                    print(f"Jarvis (Voice): {text}")
                    
                    with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"{datetime.datetime.now()}: Processing: {text[:50]}...\n")
                    
                    # Initialize engine FRESH for each utterance to avoid state issues
                    try:
                        engine = pyttsx3.init(driverName='sapi5')
                        engine.setProperty('rate', 175)
                        engine.setProperty('volume', 1.0)
                        
                        # Select male voice
                        voices = engine.getProperty('voices')
                        for voice in voices:
                            if "david" in voice.name.lower() or "male" in voice.name.lower():
                                engine.setProperty('voice', voice.id)
                                print(f"Using voice: {voice.name}")
                                break
                                
                        # Speak
                        engine.say(text)
                        engine.runAndWait()
                        
                        # Explicitly clean up
                        del engine
                        
                        with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"{datetime.datetime.now()}: Speech completed successfully\n")
                            
                    except Exception as e_engine:
                        with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"{datetime.datetime.now()}: Engine error: {e_engine}\n")
                        print(f"Engine error: {e_engine}")
                    
                    # Check if we were interrupted (using the new flag)
                    if not self.interrupt: # Check the new interrupt flag
                        # Speech completed successfully
                        if callback:
                            callback()
                    else:
                        with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"{datetime.datetime.now()}: Speech interrupted\n")
                    
                    self.is_speaking = False
                    self.speech_queue.task_done()
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
                        f.write(f"{datetime.datetime.now()}: ERROR in worker loop: {e}\n")
                    
                    print(f"SpeechOut Error: {e}")
                    self.is_speaking = False
                    if 'callback' in locals() and callback:
                        callback()
                    
            pythoncom.CoUninitialize()
            
        except Exception as e:
            with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.datetime.now()}: FATAL ERROR in worker thread: {e}\n")
            
            print(f"SpeechOut Worker Fatal Error: {e}")
            import traceback
            traceback.print_exc()

    def speak(self, text, on_complete=None):
        """
        Queue text to be spoken
        
        Args:
            text: Text to speak
            on_complete: Optional callback function to call when speech completes
        """
        # Log to file
        import datetime
        with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()}: SpeechOut.speak() called\n")
            f.write(f"  Text: {text[:100] if text else 'None'}...\n")
            f.write(f"  Has callback: {on_complete is not None}\n")
            f.write(f"  Queue size: {self.speech_queue.qsize()}\n")
        
        if not text:
            if on_complete:
                on_complete()
            return
        
        # Clear the queue if there's pending speech (interrupt)
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
        
        # Add new speech to queue
        self.speech_queue.put((text, on_complete))
        
        with open("c:/Users/lenovo/jarvis_debug.log", "a", encoding="utf-8") as f:
            f.write(f"  Added to queue, new size: {self.speech_queue.qsize()}\n")

    def stop(self):
        """
        Stop current speech and clear queue
        """
        print("SpeechOut: Stopping speech...")
        
        # Set interrupt flag
        self.interrupt = True
        
        # Clear the queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
        
        print(f"SpeechOut: Cleared queue, interrupt flag set")
        
        # Try to stop the engine if it's running (this is tricky with pyttsx3 in a thread)
        # We rely on the worker checking 'self.interrupt' after each sentence, 
        # but for long sentences, we can't easily break mid-utterance without a more complex engine wrapper.
        # However, clearing the queue ensures no FURTHER speech happens.

    def shutdown(self):
        """Shutdown the speech worker"""
        self.speech_queue.put((None, None))  # Send shutdown signal
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
