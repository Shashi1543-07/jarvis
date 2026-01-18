import cv2
import time
import os
import sys

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.vision.gesture_engine import GestureEngine

def test_gestures():
    print("--- Testing Gesture Detection ---")
    engine = GestureEngine()
    
    # Try to open camera for live test
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Camera active. Please show a Thumbs Up, Peace sign, or Stop gesture.")
    print("Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        res = engine.detect_gesture(frame)
        display_frame = frame.copy()
        
        if res["success"]:
            gesture = res["gesture"]
            print(f"Detected: {gesture}")
            engine.draw_landmarks(display_frame, res["landmarks"])
            cv2.putText(display_frame, f"Gesture: {gesture}", (10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Gesture Test", display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_gestures()
