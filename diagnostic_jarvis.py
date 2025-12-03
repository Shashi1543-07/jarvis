"""
Diagnostic wrapper to trace speech calls
"""
import sys
import os

# Monkey-patch the speech_out module to add extra logging
original_path = sys.path.copy()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

from inputs import speech_out

original_speak = speech_out.SpeechOut.speak

def logged_speak(self, text, on_complete=None):
    print(f"\n{'='*60}")
    print(f"DIAGNOSTIC: speak() called!")
    print(f"  Text: {text[:100]}")
    print(f"  Has callback: {on_complete is not None}")
    print(f"  Queue size before: {self.speech_queue.qsize()}")
    print(f"{'='*60}\n")
    
    # Call original
    result = original_speak(self, text, on_complete)
    
    print(f"DIAGNOSTIC: speak() returned, queue size: {self.speech_queue.qsize()}")
    return result

# Apply monkey patch
speech_out.SpeechOut.speak = logged_speak

print("="*60)
print("DIAGNOSTIC MODE ENABLED")
print("All speech_out.speak() calls will be logged")
print("="*60)

# Now run the normal app
sys.path = original_path
os.chdir(os.path.join(os.path.dirname(__file__), 'jarvis'))
exec(open('app.py').read())
