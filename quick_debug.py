import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

from core.nlu.intent_classifier import get_classifier

c = get_classifier()

tests = [
    "Open Chrome",
    "Close Notepad",
    "Set volume to 50",
    "Increase brightness by 20",
    "Shutdown the computer",
    "Search for python tutorials",
    "Remember my favorite color is blue",
    "Read the screen",
    "What do you see",
    "Hello"
]

for t in tests:
    r = c.classify(t)
    print(f"{t}: intent={r.get('intent')}, slots={r.get('slots')}")
