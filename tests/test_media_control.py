import sys
import os
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.router import Router

def test_media_control():
    print("--- Testing Media Control ---")
    router = Router()
    
    commands = [
        "Jarvis, play some music.",
        "Skip to the next song.",
        "Turn the volume up.",
        "Pause the playback.",
        "Stop the music."
    ]
    
    for text in commands:
        print(f"\nUser: {text}")
        res = router.route(text)
        print(f"Jarvis: {res['text']}")

if __name__ == "__main__":
    test_media_control()
