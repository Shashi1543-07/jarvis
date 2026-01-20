"""
Simple test to verify the enhanced audio engine is working
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from jarvis.core.audio_engine import AudioEngine
import time

def simple_test():
    print("Testing Enhanced Audio Engine...")
    
    # Create and start the engine
    engine = AudioEngine()
    
    # Add a simple callback to see text updates
    def text_callback(user_type, text):
        print(f"RECEIVED: [{user_type}] {text}")
    
    engine.on_text_update = text_callback
    
    try:
        print("Starting engine...")
        engine.start()
        
        print("Engine started! Waiting for voice input...")
        print("Try speaking clearly now. The system should detect your voice.")
        
        # Keep running for 60 seconds to test
        for i in range(60):
            current_state = engine.state_machine.get_state()
            if i % 10 == 0:  # Print every 10 seconds
                print(f"Status: Running... Current state: {current_state.value}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping engine...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.stop()
        print("Engine stopped.")

if __name__ == "__main__":
    simple_test()