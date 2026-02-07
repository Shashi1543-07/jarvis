"""
Quick test for Edge TTS voice
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

# Test 1: Check imports
print("Test 1: Checking imports...")
try:
    from core.voice.edge_tts_engine import EdgeTTSEngine, EDGE_TTS_AVAILABLE
    print(f"  Edge TTS available: {EDGE_TTS_AVAILABLE}")
except ImportError as e:
    print(f"  Import error: {e}")

# Test 2: Check SpeechOut
print("\nTest 2: Checking SpeechOut...")
try:
    from inputs.speech_out import SpeechOut
    speech = SpeechOut()
    print(f"  SpeechOut initialized")
    print(f"  Using Edge TTS: {speech.use_edge_tts}")
except Exception as e:
    print(f"  Error: {e}")

# Test 3: Check anti-repetition templates
print("\nTest 3: Checking anti-repetition system...")
try:
    from core.local_brain import LocalBrain
    from core.memory import Memory
    
    mem = Memory()
    brain = LocalBrain(mem)
    
    # Get 5 greetings - should all be different
    greetings = []
    for i in range(5):
        g = brain._get_unique_response("GREETING")
        greetings.append(g)
        print(f"  Greeting {i+1}: {g}")
    
    # Check for duplicates
    unique = len(set(greetings))
    print(f"\n  Unique greetings: {unique}/5 (expected: 5)")
    
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Voice Enhancement Tests Complete ===")
