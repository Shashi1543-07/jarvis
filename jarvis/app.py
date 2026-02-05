import sys
import os
import time

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    # Force unbuffered output
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("Initializing Jarvis AI...", flush=True)
    # TODO: Load configuration
    # Initialize modules
    from core.router import Router
    
    router = Router()
    print("Router initialized.")
    
    # Voice mode setup (using new AudioEngine)
    voice_mode = True

    # GUI Mode Selection (Hardcoded to True for this phase, can be arg)
    USE_GUI = True
    
    engine = None
    if voice_mode:
        print("Initializing Audio Engine...")
        from core.audio_engine import AudioEngine
        engine = AudioEngine(router=router)
        engine.start()
        print("Realtime Audio Engine started.")

        # Start Proactive Heartbeat
        try:
            from core.heartbeat import start_heartbeat
            start_heartbeat(engine)
            print("Proactive Heartbeat initialized.")
        except Exception as e:
            print(f"Failed to start Heartbeat: {e}")

    if USE_GUI:
        print("Starting GUI...")
        from gui_hologram import JarvisGUI
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        gui = JarvisGUI(engine)
        gui.show()
        
        print("GUI launched. Close window to exit.")
        sys.exit(app.exec_())
    
    # If no GUI, run appropriate mode
    if voice_mode:
        # Voice mode without GUI - keep thread alive
        print(f"Jarvis is ready in VOICE mode (no GUI)")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            if engine:
                engine.stop()
            print("\nJarvis: Shutting down...")
    else:
        # Text mode loop
        print(f"Jarvis is ready in TEXT mode")
        try:
            while True:
                user_input = input("You: ")
                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit", "bye", "stop"]:
                    print("Jarvis: Goodbye, sir.")
                    break
                
                response = router.route(user_input)
                print(f"Jarvis: {response['text']}")
                
        except KeyboardInterrupt:
            print("\nJarvis: Shutting down...")

if __name__ == "__main__":
    main()
