import sys
import os
import time
import threading

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.voice.realtime import RealtimeVoicePipeline
from core.router import Router

def mock_route(text):
    print(f"MOCK ROUTER: Received '{text}'")
    return {"action": "speak", "text": f"I heard you say: {text}"}

def main():
    print("Initializing Voice Pipeline Verification...")
    
    pipeline = RealtimeVoicePipeline()
    
    # Mock the internal router for testing
    # We need to monkeypatch the instance's router
    pipeline.router.route = mock_route
    
    # Start in thread (pipeline.start() spawns its own thread now, but let's call it directly)
    pipeline.start()
    
    print("Pipeline started. Speak into the microphone.")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        pipeline.stop()

if __name__ == "__main__":
    main()
