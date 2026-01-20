import numpy as np
import sys
import os

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.voice.aec_enhanced import EnhancedAECWithNR
from core.voice.noise_suppression import AdaptiveNoiseSuppressor

def test_audio_pipeline():
    print("Testing Audio Pipeline...")
    
    aec = EnhancedAECWithNR(frame_size=512, filter_length=1024)
    ns = AdaptiveNoiseSuppressor(sample_rate=16000)
    
    # Create a dummy voice-like signal (sine wave + noise)
    fs = 16000
    t = np.linspace(0, 512/fs, 512)
    mic_signal = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(512)
    mic_signal = (mic_signal * 32768).astype(np.int16)
    mic_bytes = mic_signal.tobytes()
    
    ref_signal = 0.1 * np.sin(2 * np.pi * 440 * t)
    ref_signal = (ref_signal * 32768).astype(np.int16)
    ref_bytes = ref_signal.tobytes()
    
    # 1. Test AEC
    print("Testing AEC...")
    clean_bytes, erl = aec.process_with_noise_reduction(mic_bytes, ref_bytes)
    clean_signal = np.frombuffer(clean_bytes, dtype=np.int16)
    
    rms_in = np.sqrt(np.mean(mic_signal.astype(np.float32)**2))
    rms_out = np.sqrt(np.mean(clean_signal.astype(np.float32)**2))
    
    print(f"AEC RMS In: {rms_in:.2f}, Out: {rms_out:.2f}, ERL: {erl:.2f}")
    
    if rms_out < 1.0:
        print("FAILED: AEC zeroed out the signal!")
        return False
        
    # 2. Test Noise Suppression
    print("Testing NS...")
    # Feed some frames to let it "learn"
    for _ in range(30):
        ns.process_frame(mic_bytes)
    
    ns_bytes = ns.process_frame(mic_bytes)
    ns_signal = np.frombuffer(ns_bytes, dtype=np.int16)
    rms_ns = np.sqrt(np.mean(ns_signal.astype(np.float32)**2))
    
    print(f"NS RMS In: {rms_in:.2f}, Out: {rms_ns:.2f}")
    
    if rms_ns < 1.0:
        print("FAILED: NS zeroed out the signal!")
        return False
        
    print("SUCCESS: Audio pipeline is preserving signal integrity.")
    return True

if __name__ == "__main__":
    success = test_audio_pipeline()
    if not success:
        sys.exit(1)
    sys.exit(0)
