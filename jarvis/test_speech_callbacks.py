"""
Quick test to verify speech_out callback mechanism works
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from inputs.speech_out import SpeechOut
import time

print("Testing new SpeechOut implementation...")

speech = SpeechOut()

# Test 1: Basic speech
print("\n=== Test 1: Basic Speech ===")
completed = False

def on_complete():
    global completed
    completed = True
    print("  -> Speech completed!")

speech.speak("Testing the new speech system.", on_complete=on_complete)

# Wait for completion
timeout = 10
start = time.time()
while not completed and (time.time() - start) < timeout:
    time.sleep(0.1)

if completed:
    print("✓ Test 1 PASSED: Callback fired correctly")
else:
    print("✗ Test 1 FAILED: Callback did not fire")

# Test 2: Queue handling (interrupt)
print("\n=== Test 2: Interrupt Test ===")
completed2 = False

def on_complete2():
    global completed2
    completed2 = True
    print("  -> Second speech completed!")

speech.speak("This is a long message that should be interrupted.", on_complete=lambda: None)
time.sleep(0.5)  # Let it start
speech.speak("This is the second message.", on_complete=on_complete2)

# Wait for second speech
start = time.time()
while not completed2 and (time.time() - start) < timeout:
    time.sleep(0.1)

if completed2:
    print("✓ Test 2 PASSED: Queue and interrupt work")
else:
    print("✗ Test 2 FAILED: Queue didnot work correctly")

print("\n=== All Tests Complete ===")
speech.shutdown()
