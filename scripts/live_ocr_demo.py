import cv2
import sys
import os
import json
import time

# Add project paths
sys.path.insert(0, os.path.join(os.getcwd(), 'jarvis'))
sys.path.insert(0, os.getcwd())

from actions import vision_actions
from vision.utils import get_camera

def run_live_ocr():
    print("="*80)
    print("JARVIS LIVE OCR DEMO")
    print("="*80)
    print("Starting vision system... Press 'q' to quit.")
    
    # Open camera via vision_actions (which also starts the background thread)
    vision_actions.open_camera()
    cam = get_camera()
    
    try:
        while True:
            frame = cam.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Display frame
            display_frame = frame.copy()
            
            # Run OCR on the frame (requested structured output)
            # We call the new function in vision_actions
            json_output = vision_actions.read_text_from_frame(frame)
            results = json.loads(json_output)
            
            # Draw bounding boxes and text
            for res in results:
                bbox = res['bounding_box']
                text = res['detected_text']
                conf = res['confidence']
                
                # [x, y, w, h]
                x, y, w, h = bbox
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(display_frame, f"{text} ({conf:.2f})", (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imshow("JARVIS Vision - Live OCR", display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        vision_actions.close_camera()
        cv2.destroyAllWindows()
        print("Vision system closed.")

if __name__ == "__main__":
    run_live_ocr()
