import pyttsx3
import speech_recognition as sr
import sys

def test_tts():
    print("Testing TTS...")
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"Found {len(voices)} voices.")
        for v in voices:
            print(f" - {v.name}")
        
        print("Speaking...")
        engine.say("This is a test of the voice system.")
        engine.runAndWait()
        print("TTS success.")
    except Exception as e:
        print(f"TTS failed: {e}")
        import traceback
        traceback.print_exc()

def test_stt():
    print("\nTesting STT...")
    r = sr.Recognizer()
    try:
        mics = sr.Microphone.list_microphone_names()
        print(f"Found microphones: {mics}")
        
        with sr.Microphone() as source:
            print("Adjusting for noise... (Please be silent)")
            r.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold: {r.energy_threshold}")
            
            print("Speak something now...")
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("Processing...")
            try:
                text = r.recognize_google(audio)
                print(f"Heard: {text}")
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Google Speech API error: {e}")
    except Exception as e:
        print(f"STT failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tts()
    test_stt()
