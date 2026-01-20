#!/usr/bin/env python3
"""
Simple microphone test to verify audio input is working
"""
import pyaudio
import numpy as np
import time

def test_microphone():
    print("Testing microphone input...")
    
    # Configuration
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    TEST_DURATION = 5  # seconds

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    try:
        # Open stream
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        print(f"Microphone opened: {RATE}Hz, {CHANNELS} channel(s)")
        print(f"Recording for {TEST_DURATION} seconds. Speak during this time...")
        print("-" * 50)
        
        # Record for specified duration
        start_time = time.time()
        sample_count = 0
        
        while time.time() - start_time < TEST_DURATION:
            # Read audio data
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # Convert to numpy array
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            
            # Calculate RMS (Root Mean Square) - measure of audio power
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Calculate peak amplitude
            peak = np.max(np.abs(audio_data))
            
            # Print status every second or when there's significant audio
            sample_count += 1
            if sample_count % (RATE // CHUNK) == 0:  # Every second
                print(f"Time: {int(time.time() - start_time)}s | RMS: {rms:.4f} | Peak: {peak:.2f}")
            
            # Alert if audio level is high enough
            if rms > 0.01:  # Significant audio detected
                print(f"  >>> AUDIO DETECTED: RMS={rms:.4f}, Peak={peak:.2f}")
        
        print("-" * 50)
        print("Test completed. If you spoke during the test, you should have seen 'AUDIO DETECTED' messages.")
        print("If not, there may be an issue with your microphone or audio drivers.")
        
    except Exception as e:
        print(f"Error during microphone test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        try:
            stream.stop_stream()
            stream.close()
        except:
            pass
        p.terminate()

if __name__ == "__main__":
    test_microphone()