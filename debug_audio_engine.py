"""
Debug script to test the enhanced audio engine
This will help diagnose why the system isn't responding to your voice
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from jarvis.core.audio_engine import AudioEngine
import time
import threading

def test_audio_engine():
    print("Starting Audio Engine Debug Test...")
    print("="*50)
    
    # Create audio engine
    engine = AudioEngine()
    
    # Set up text update callback to see what's happening
    def on_text_update(user_type, text):
        print(f"[{user_type.upper()}]: {text}")
    
    engine.on_text_update = on_text_update
    
    try:
        # Start the engine
        print("Starting audio engine...")
        engine.start()
        
        print("\nEngine started successfully!")
        print(f"Current state: {engine.state_machine.get_state().value}")
        print("\nSpeak clearly and loudly now...")
        print("Say 'hello' or 'test' to see if the system detects your voice")
        print("Say 'go to sleep' to test sleep mode")
        print("Say 'wake up' to test wake from sleep")
        print("\nListening for 30 seconds...")
        
        # Listen for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            time.sleep(1)
            current_state = engine.state_machine.get_state().value
            if current_state != "prev_state":
                print(f"State changed to: {current_state}")
        
        print("\n30-second test completed.")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("Stopping audio engine...")
        engine.stop()
        print("Test completed.")

def test_microphone_only():
    """Test just the microphone to see if it's picking up audio"""
    print("Testing microphone input only...")
    from jarvis.core.voice.mic import Microphone
    import numpy as np
    
    mic = Microphone()
    mic.start()
    
    print("Recording for 5 seconds. Speak during this time...")
    for i in range(5):
        chunk = mic.read_chunk()
        if chunk:
            # Calculate RMS to see if audio is being captured
            audio_data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
            rms = np.sqrt(np.mean(audio_data**2))
            print(f"Second {i+1}: RMS = {rms:.4f}")
        time.sleep(1)
    
    mic.stop()
    print("Microphone test completed.")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Full audio engine test")
    print("2. Microphone only test")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_audio_engine()
    elif choice == "2":
        test_microphone_only()
    else:
        print("Invalid choice. Running full audio engine test...")
        test_audio_engine()