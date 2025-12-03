import speech_recognition as sr

class SpeechIn:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust recognizer settings for better sensitivity
        self.recognizer.energy_threshold = 300  # Lower threshold for quieter speech
        self.recognizer.dynamic_energy_threshold = True  # Adapt to noise levels
        self.recognizer.pause_threshold = 0.8  # Reduced from 2.0 for faster response
        self.recognizer.non_speaking_duration = 0.5 # Faster cutoff
        
        print("Calibrating microphone for ambient noise... Please wait.")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print(f"Microphone calibrated. Energy threshold: {self.recognizer.energy_threshold}")

    def listen(self):
        print("Listening...")
        try:
            with self.microphone as source:
                # Re-adjust for ambient noise periodically (very short)
                # self.recognizer.adjust_for_ambient_noise(source, duration=0.1) 
                # Commented out to reduce loop latency; initial calibration should suffice for stable environments
                
                # Increased timeout and phrase limit for longer commands
                # phrase_time_limit=None allows indefinite listening until silence
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=None)
            
            print("Recognizing...")
            text = self.recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None
        except Exception as e:
            print(f"Error listening: {e}")
            return None
