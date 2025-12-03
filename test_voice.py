import pyttsx3
import pythoncom
import threading
import time

def test_voice():
    print("Testing voice...")
    try:
        # Initialize COM
        pythoncom.CoInitialize()
        
        engine = pyttsx3.init(driverName='sapi5')
        voices = engine.getProperty('voices')
        print(f"Found {len(voices)} voices.")
        for v in voices:
            print(f" - {v.name}")
            
        engine.setProperty('rate', 170)
        engine.setProperty('volume', 1.0)
        
        print("Speaking...")
        engine.say("This is a test of the Jarvis voice system.")
        engine.runAndWait()
        print("Speech complete.")
        
        pythoncom.CoUninitialize()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    t = threading.Thread(target=test_voice)
    t.start()
    t.join()
    print("Test finished.")
