"""
Vision Actions - Complete Vision AI System for JARVIS
Integrates all vision capabilities: object detection, face recognition, scene description, emotions, search
"""

import cv2
import os
import datetime
import time
import threading
import numpy as np

# Import vision modules
from core.vision.face_manager import FaceManager
from core.vision.yolo_detector import YOLODetector
from core.vision.scene_description import SceneDescriptor
from core.vision.emotion_detector import EmotionDetector
from core.vision.internet_search import search_object_info, search_and_summarize

# Import camera utilities
from vision.utils import get_camera

# Legacy imports for backward compatibility
try:
    import mediapipe as mp
except ImportError:
    mp = None
try:
    import pytesseract
except ImportError:
    pytesseract = None
try:
    from pyzbar.pyzbar import decode as qr_decode
except ImportError:
    qr_decode = None

# ============================================================================
# GLOBAL STATE & SINGLETONS
# ============================================================================

# Vision module instances (lazy loaded)
_face_manager = None
_yolo_detector = None
_scene_descriptor = None
_emotion_detector = None
_ocr_engine = None
_gesture_engine = None
_pose_guard = None

# Global vision thread state
_vision_state = {
    "active_modes": set(),  # e.g., {'object_detection', 'face_recognition'}
    "thread": None,
    "running": False,
    "lock": threading.Lock(),
    "current_frame": None,  # Store latest frame for queries
    "latest_summary": "Nothing detected yet.",
    "latest_gesture": {"success": False, "gesture": "None"},
    "last_update_time": 0,
    "history": [] # List of (timestamp, summary) tuples
}

def _get_face_manager():
    """Lazy load face manager"""
    global _face_manager
    if _face_manager is None:
        _face_manager = FaceManager()
    return _face_manager

def _get_yolo_detector():
    """Lazy load YOLO detector"""
    global _yolo_detector
    if _yolo_detector is None:
        _yolo_detector = YOLODetector()
    return _yolo_detector

def _get_scene_descriptor():
    """Lazy load scene descriptor"""
    global _scene_descriptor
    if _scene_descriptor is None:
        _scene_descriptor = SceneDescriptor()
    return _scene_descriptor

def _get_emotion_detector():
    """Lazy load emotion detector"""
    global _emotion_detector
    if _emotion_detector is None:
        _emotion_detector = EmotionDetector()
    return _emotion_detector

def _get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from core.vision.ocr_engine import OCREngine
        _ocr_engine = OCREngine()
    return _ocr_engine

def _get_gesture_engine():
    global _gesture_engine
    if _gesture_engine is None:
        from core.vision.gesture_engine import GestureEngine
        _gesture_engine = GestureEngine()
    return _gesture_engine

def _get_pose_guard():
    global _pose_guard
    if _pose_guard is None:
        from core.vision.pose_guard import PostureGuard
        _pose_guard = PostureGuard()
    return _pose_guard

# ============================================================================
# CORE CAMERA FUNCTIONS
# ============================================================================

def open_camera(camera_id=0):
    """
    Turn on webcam with live feed
    
    Returns:
        str: Status message
    """
    print(f"Opening camera {camera_id}...")
    _start_vision_thread()
    return f"Camera is now active. I can see the world, sir."

def close_camera():
    """
    Release webcam and stop vision thread
    
    Returns:
        str: Status message
    """
    print("Closing camera...")
    _vision_state["running"] = False
    _vision_state["active_modes"].clear()
    
    if _vision_state["thread"]:
        _vision_state["thread"].join(timeout=2)
        _vision_state["thread"] = None
    
    # Force close camera
    cam = get_camera()
    cam.close_camera()
    
    return "Camera closed, sir."

def capture_photo(filename=None):
    """
    Take a snapshot from camera
    
    Args:
        filename: Optional filename for the photo
        
    Returns:
        str: Path to saved photo
    """
    print("Capturing photo...")
    cam = get_camera()
    
    if not cam.open_camera():
        return "Camera not available."
    
    # Wait for auto-exposure if just opened
    if not _vision_state["running"]:
        time.sleep(1)
    
    frame = cam.get_frame()
    if frame is not None:
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
        
        save_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        cv2.imwrite(filepath, frame)
        
        # Close if we opened it just for this
        if not _vision_state["running"]:
            cam.close_camera()
        
        return f"Photo saved to {filepath}"
    
    return "Failed to capture frame."

# ============================================================================
# VISION ANALYSIS HELPERS
# ============================================================================

def analyze_scene(prompt="What's on the screen?", **kwargs):
    """
    General purpose analysis using Vision AI.
    If 'screen' is in prompt, assumes screen capture. Otherwise, uses camera.
    """
    # 1. Check if this is a SCREEN request
    if "screen" in prompt.lower():
        import pyautogui
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screen_{timestamp}.png"
            save_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(save_dir, exist_ok=True)
            filepath = os.path.join(save_dir, filename)

            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filepath, screenshot_cv)

            # Use EasyOCR for screen content
            try:
                import easyocr
                reader = easyocr.Reader(['en'])
                result = reader.readtext(screenshot_cv)
                extracted_text = " ".join([item[1] for item in result if item[1].strip()])
                
                return {
                    "text": extracted_text[:1000], 
                    "screenshot_path": filepath,
                    "type": "screen_analysis"
                }
            except ImportError:
                 # Fallback to Tesseract if EasyOCR fails
                try:
                    import pytesseract
                    # Check if tesseract is in path or set it?
                    # Assuming default for now or user has it
                    text = pytesseract.image_to_string(screenshot_cv)
                    return {
                        "text": text[:1000],
                        "screenshot_path": filepath,
                        "type": "screen_analysis"
                    }
                except ImportError:
                    return {"error": "No OCR engine available (EasyOCR/Tesseract)."}

        except Exception as e:
            return {"error": str(e)}
    
    # 2. Otherwise its a CAMERA request (Scene/Objects/People)
    else:
        # Re-use specific functions for camera analysis to keep logic clean
        # or implement a generic camera analysis here using BLIP/YOLO
        
        # Determine intent from prompt
        prompt_lower = prompt.lower()
        
        if "read" in prompt_lower or "text" in prompt_lower:
            return read_text(prompt, **kwargs)
            
        elif "object" in prompt_lower or "detect" in prompt_lower:
             # Inline logic from old detect_objects to avoid recursion loop if detect_objects calls this
            frame = _get_current_frame()
            if frame is None: return {"error": "Camera not active."}
            detector = _get_yolo_detector()
            results = detector.detect(frame)
            return results
            
        elif "scene" in prompt or "describe" in prompt_lower:
             # Inline logic from old describe_scene
            frame = _get_current_frame()
            if frame is None: return {"error": "Camera not active."}
            descriptor = _get_scene_descriptor()
            return descriptor.describe(frame)
            
        elif "people" in prompt_lower or "who" in prompt_lower:
            # Inline logic from old identify_people
            frame = _get_current_frame()
            if frame is None: return {"error": "Camera not active."}
            face_mgr = _get_face_manager()
            results = face_mgr.recognize_faces(frame)
            # transform results to expected dict
            names = [r['name'] for r in results] if results else []
            msg = f"I see {', '.join(names)}" if names else "I don't see anyone."
            return {"type": "identify_people", "message": msg, "people": names}

        return {"error": "Could not determine analysis type from prompt."}

# ============================================================================
# OBJECT DETECTION (YOLO)
# ============================================================================

def detect_objects(**kwargs):
    """
    List objects visible in the camera frame.
    """
    prompt = kwargs.pop('prompt', "List the objects visible in this frame.")
    return analyze_scene(prompt=prompt, **kwargs)

def detect_handheld_object():
    """
    Advanced identification of a specific object being held.
    Uses local YOLO detection and BLIP scene description for multi-stage analysis.
    """
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active."}

    # 1. Try local YOLO object detection for specific identification
    detector = _get_yolo_detector()
    yolo_results = detector.detect(frame)
    
    # 2. Try BLIP for natural scene context
    descriptor = _get_scene_descriptor()
    blip_result = descriptor.describe(frame)

    summary_data = {
        "yolo_detections": yolo_results.get('details', []),
        "scene_description": blip_result.get('description', ""),
        "type": "handheld_analysis"
    }

    # Return structured data for the Brain to summarize
    return summary_data

def is_object_present(object_name):
    """
    Check if a specific object is visible
    
    Args:
        object_name: Object to look for (e.g., "laptop", "person", "bottle")
        
    Returns:
        dict: Presence status
    """
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active."}
    
    detector = _get_yolo_detector()
    result = detector.is_object_present(frame, object_name)
    
    if result['present']:
        count = result['count']
        message = f"Yes, I can see {count} {object_name}{'s' if count > 1 else ''}."
    else:
        message = f"No, I don't see any {object_name} right now."
    
    return {
        "object": object_name,
        "present": result['present'],
        "count": result['count'],
        "message": message
    }

def count_objects(object_name=None):
    """
    Count objects (specific type or all objects)
    
    Args:
        object_name: Optional object type to count
        
    Returns:
        dict: Count information
    """
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active."}
    
    detector = _get_yolo_detector()
    result = detector.count_objects(frame, object_name)
    
    if object_name:
        count = result['count']
        message = f"I count {count} {object_name}{'s' if count > 1 else ''}."
        return {
            "object": object_name,
            "count": count,
            "message": message
        }
    else:
        total = result['total']
        objects = result['objects']
        obj_list = [f"{v} {k}{'s' if v > 1 else ''}" for k, v in objects.items()]
        message = f"I count {total} objects total: {', '.join(obj_list)}."
        return {
            "total": total,
            "objects": objects,
            "message": message
        }

def object_detection():
    """
    Enable object detection overlay mode
    
    Returns:
        str: Status message
    """
    _start_vision_thread()
    _vision_state["active_modes"].add("object_detection")
    return "Object detection enabled. I'm analyzing objects in real-time."

# ============================================================================
# FACE RECOGNITION & MEMORY
# ============================================================================

def identify_people(**kwargs):
    """
    Identify people in the frame.
    """
    prompt = kwargs.pop('prompt', "Identify the people in this frame. Who is this?")
    return analyze_scene(prompt=prompt, **kwargs)

def who_is_in_front():
    """
    Tell who is currently in front of the camera
    
    Returns:
        dict: Person identification
    """
    return identify_people()

def remember_face(name):
    """
    Learn and remember a new face
    
    Args:
        name: Name of the person to remember
        
    Returns:
        dict: Learning result
    """
    print(f"Learning face for: {name}")
    
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active. Please open camera first."}
    
    face_mgr = _get_face_manager()
    result = face_mgr.learn_face(frame, name)
    
    return result

def face_recognition(person_name=None):
    """
    Enable face recognition mode
    
    Args:
        person_name: Optional name to look for specifically
        
    Returns:
        str: Status message
    """
    _start_vision_thread()
    _vision_state["active_modes"].add("face_recognition")
    return "Face recognition enabled. I'm scanning for faces."

# ============================================================================
# SCENE DESCRIPTION
# ============================================================================

def describe_scene(**kwargs):
    """
    Describe the scene in front of the camera.
    """
    prompt = kwargs.pop('prompt', "Describe the scene in detail.")
    return analyze_scene(prompt=prompt, **kwargs)

def scene_description():
    """Alias for describe_scene"""
    return describe_scene()

# ============================================================================
# EMOTION RECOGNITION
# ============================================================================

def detect_emotion():
    """
    Detect emotion from facial expression
    
    Returns:
        dict: Emotion analysis
    """
    print("Detecting emotion...")
    
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active."}
    
    emotion_det = _get_emotion_detector()
    result = emotion_det.detect_emotion(frame)
    
    if 'error' in result:
        return result
    
    emotion = result['emotion']
    confidence = result['confidence']
    
    # Format message
    if confidence > 0.7:
        message = f"You look {emotion}."
    elif confidence > 0.5:
        message = f"You seem {emotion}."
    else:
        message = f"I'm not quite sure, but maybe {emotion}?"
    
    return {
        "emotion": emotion,
        "confidence": confidence,
        "message": message,
        **result
    }

def emotion_detection():
    """
    Enable emotion detection mode
    
    Returns:
        str: Status message
    """
    _start_vision_thread()
    _vision_state["active_modes"].add("emotion_detection")
    return "Emotion detection enabled. I'm reading facial expressions."

# ============================================================================
# INTERNET SEARCH FOR OBJECTS
# ============================================================================

def search_object_details(object_name=None):
    """
    Search internet for information about a detected object
    
    Args:
        object_name: Object to search for (if None, detects first object)
        
    Returns:
        dict: Search results and summary
    """
    print(f"Searching for object info: {object_name}")
    
    # If no object specified, detect one
    if not object_name:
        frame = _get_current_frame()
        if frame is None:
            return {"error": "Camera not active."}
        
        detector = _get_yolo_detector()
        results = detector.detect(frame)
        
        if not results.get('objects'):
            return {"error": "No objects detected. Please specify an object."}
        
        # Use first detected object
        object_name = results['objects'][0]
        print(f"Detected object: {object_name}, searching...")
    
    # Search for object
    search_results = search_and_summarize(object_name, use_llm=True)
    
    if 'error' in search_results:
        return search_results
    
    return {
        "object": object_name,
        "summary": search_results['summary'],
        "message": search_results['summary']
    }

# ============================================================================
# OCR & TEXT EXTRACTION
# ============================================================================

def read_text(prompt="Read the text.", **kwargs):
    """
    Robust OCR using the new OCREngine.
    """
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active."}

    try:
        engine = _get_ocr_engine()
        results = engine.detect_and_read(frame)

        extracted_text = " ".join([item['detected_text'] for item in results if item['detected_text'].strip()])

        if extracted_text.strip():
            return {
                "text": extracted_text, 
                "details": results,
                "message": f"I extracted the following text: {extracted_text}",
                "type": "ocr_result"
            }
        else:
            # SAVE DEBUG FRAME
            debug_path = os.path.join(os.getcwd(), "debug_ocr_failed.jpg")
            cv2.imwrite(debug_path, frame)
            return {
                "text": "No text detected.",
                "message": f"I couldn't identify any clear text. I've saved the camera view to {debug_path} for inspection.",
                "type": "ocr_result"
            }
    except Exception as e:
        return {"error": f"OCR Engine failed: {str(e)}"}

def read_text_from_frame(frame):
    """
    Detect and read text from a specific frame.
    Returns: JSON structured output as a string.
    """
    try:
        engine = _get_ocr_engine()
        return engine.read_text_from_frame(frame)
    except Exception as e:
        import json
        return json.dumps({"error": str(e)})

def ocr_extract_text(image_path=None):
    """Legacy Tesseract OCR (kept for speed if needed)"""
    if pytesseract is None:
        return "PyTesseract not installed."
    
    if not image_path:
        frame = _get_current_frame()
        if frame is None:
            return "Camera not active."
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        return f"Extracted text: {text}"
    else:
        if os.path.exists(image_path):
            img = cv2.imread(image_path)
            text = pytesseract.image_to_string(img)
            return f"Extracted text: {text}"
        return "File not found."

# ============================================================================
# SCREEN ANALYSIS (LLM Vision)
# ============================================================================

# ============================================================================
# SCREEN ANALYSIS HELPERS
# ============================================================================

def read_screen(**kwargs):
    """Extract all text from screen"""
    prompt = kwargs.pop('prompt', "Extract all text visible on this screen.")
    return analyze_scene(prompt=prompt, **kwargs)

def describe_screen(**kwargs):
    """Describe what's on the screen"""
    prompt = kwargs.pop('prompt', "Describe what you see on this screen in detail.")
    return analyze_scene(prompt=prompt, **kwargs)

def identify_ui_elements(**kwargs):
    """Identify clickable UI elements"""
    prompt = kwargs.pop('prompt', "Identify all clickable UI elements (buttons, links, inputs) on the screen.")
    return analyze_scene(prompt=prompt, **kwargs)

def analyze_error(**kwargs):
    """Analyze errors on screen"""
    prompt = kwargs.pop('prompt', "Look for error messages on the screen and suggest fixes.")
    return analyze_scene(prompt=prompt, **kwargs)

# ============================================================================
# ADDITIONAL VISION MODES
# ============================================================================

def deep_scan():
    """
    The ultimate vision mode. Enables Object Detection, Face Recognition, 
    and Emotion analysis all at once.
    """
    with _vision_state["lock"]:
        _vision_state["active_modes"] = {"object_detection", "face_recognition", "emotion_detection"}
    _start_vision_thread()
    return "Initialising deep scan. All vision systems are now active and tracking, sir."
    _vision_state["active_modes"].add("motion_detection")
    return "Motion detection enabled. I'll alert you to movement."

def scan_qr_code():
    """Enable QR/barcode scanning mode"""
    if qr_decode is None:
        return "pyzbar not installed."
    
    _start_vision_thread()
    _vision_state["active_modes"].add("qr_scanning")
    return "QR scanner enabled. Show me a code."

def gesture_control():
    """Enable hand gesture recognition"""
    if mp is None:
        return "MediaPipe not installed."
    
    _start_vision_thread()
    _vision_state["active_modes"].add("gesture_control")
    return "Gesture control enabled. Show me your hand."

def check_posture():
    """Enable posture monitoring"""
    if mp is None:
        return "MediaPipe not installed."
    
    _start_vision_thread()
    _vision_state["active_modes"].add("posture_correction")
    return "Posture monitoring enabled. Sit up straight!"

# ============================================================================
# VISION LOOP & HELPERS
# ============================================================================

def _get_current_frame():
    """Get latest frame from camera"""
    cam = get_camera()
    
    # If vision thread running, use cached frame
    if _vision_state["running"] and _vision_state["current_frame"] is not None:
        return _vision_state["current_frame"]
    
    # Otherwise open camera and get frame
    if not cam.open_camera():
        return None
    
    frame = cam.get_frame()
    return frame

def _start_vision_thread():
    """Start background vision thread"""
    with _vision_state["lock"]:
        if not _vision_state["running"]:
            _vision_state["running"] = True
            _vision_state["thread"] = threading.Thread(target=_vision_loop, daemon=True)
            _vision_state["thread"].start()

def _vision_loop():
    """Background loop for real-time vision display"""
    cam = get_camera()
    if not cam.open_camera():
        print("Vision Loop: Could not open camera")
        return
    
    # Initialize detectors
    face_mgr = None
    yolo = None
    emotion_det = None
    gestures = None
    poses = None
    
    print("Vision Loop: Started")
    
    while _vision_state["running"]:
        frame = cam.get_frame()
        if frame is None:
            time.sleep(0.1)
            continue
        
        # Cache frame for queries
        _vision_state["current_frame"] = frame.copy()
        
        display_frame = frame.copy()
        modes = _vision_state["active_modes"].copy()
        
        # Object Detection & Summary (Always run for global context if camera is offline)
        if yolo is None:
            yolo = _get_yolo_detector()
        
        # We only draw if mode is active, but we always detect for the brain
        detect_res = yolo.detect(frame)
        if detect_res.get('objects'):
            from collections import Counter
            counts = Counter(detect_res['objects'])
            summary = ", ".join([f"{v} {k}" for k, v in counts.items()])
            _vision_state["latest_summary"] = f"Visible: {summary}"
            
            # Update history every 10 seconds or if major change
            now = time.time()
            if now - _vision_state["last_update_time"] > 10:
                _vision_state["history"].append((datetime.datetime.now(), summary))
                if len(_vision_state["history"]) > 50: _vision_state["history"].pop(0)
                _vision_state["last_update_time"] = now
        else:
            _vision_state["latest_summary"] = "Nothing of interest detected."

        if "object_detection" in modes:
            display_frame, _ = yolo.detect_and_draw(display_frame)
        
        # Face Recognition
        if "face_recognition" in modes:
            if face_mgr is None:
                face_mgr = _get_face_manager()
            
            results = face_mgr.recognize_faces(frame)
            for result in results:
                t, r, b, l = result['location']
                name = result['name']
                conf = result['confidence']
                
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(display_frame, (l, t), (r, b), color, 2)
                cv2.putText(display_frame, f"{name} ({conf:.2f})", (l, t-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Emotion Detection
        if "emotion_detection" in modes:
            if emotion_det is None:
                emotion_det = _get_emotion_detector()
            
            result = emotion_det.detect_emotion(frame)
            if result.get('success'):
                emotion = result['emotion']
                conf = result['confidence']
                cv2.putText(display_frame, f"Emotion: {emotion} ({conf:.2f})",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Gesture Recognition
        if "gesture_control" in modes:
            if gestures is None:
                gestures = _get_gesture_engine()
            
            res = gestures.detect_gesture(frame)
            if res["success"]:
                gesture_name = res["gesture"]
                gestures.draw_landmarks(display_frame, res["landmarks"])
                cv2.putText(display_frame, f"Gesture: {gesture_name}",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Store raw result for Heartbeat processing
                _vision_state["latest_gesture"] = res

                # Proactive Trigger: Thumbs up gives audio feedback
                if gesture_name == "THUMBS_UP":
                    _vision_state["latest_summary"] = "The user is giving a thumbs up. Acknowledged."

        # Posture Guard
        if "posture_guard" in modes or "check_posture" in modes:
            if poses is None:
                poses = _get_pose_guard()
            
            res = poses.check_posture(frame)
            if res["success"]:
                poses.draw_pose(display_frame, res["landmarks"])
                status = "SLOUCHING" if res["is_slouching"] else "GOOD"
                color = (0, 0, 255) if res["is_slouching"] else (0, 255, 0)
                cv2.putText(display_frame, f"Posture: {status}",
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                
                if res["is_slouching"]:
                    _vision_state["latest_summary"] = "User is slouching. I should politely recommend adjustment."
        
        # Show frame
        cv2.imshow("Jarvis Vision", display_frame)
        
        # Handle window close or 'q' press
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or cv2.getWindowProperty("Jarvis Vision", cv2.WND_PROP_VISIBLE) < 1:
            break
    
    # Cleanup
    cam.close_camera()
    cv2.destroyAllWindows()
    _vision_state["running"] = False
    _vision_state["latest_summary"] = "Camera is offline."
    print("Vision Loop: Stopped")

def get_vision_context():
    """Returns the latest vision summary for LLM context"""
    return _vision_state.get("latest_summary", "Camera is offline.")

# ============================================================================
# LEGACY COMPATIBILITY
# ============================================================================

def face_detection():
    """Legacy face detection (basic)"""
    _start_vision_thread()
    _vision_state["active_modes"].add("face_detection")
    return "Face detection enabled."

def face_register(person_name):
    """Legacy face registration"""
    return remember_face(person_name)

def object_tracking(object_name):
    """Placeholder for object tracking"""
    return f"Tracking {object_name}... (Feature in development)"

def object_count(object_name=None):
    """Alias for count_objects"""
    return count_objects(object_name)

def identify_object():
    """Identify primary object"""
    return detect_objects()

def highlight_object(object_name):
    """Highlight specific object"""
    return object_detection()

def document_scan():
    """Document scanning placeholder"""
    return "Document scanning... (Feature in development)"

def activity_recognition():
    """Activity recognition placeholder"""
    return "Activity recognition... (Feature in development)"

def record_video(duration=10, filename=None):
    """Record video clip"""
    _start_vision_thread()
    
    print(f"Recording video for {duration} seconds...")
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"video_{timestamp}.avi"
    
    save_dir = os.path.join(os.getcwd(), "screenshots")
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)
    
    cam = get_camera()
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filepath, fourcc, 20.0, (640, 480))
    
    start_time = time.time()
    while (time.time() - start_time) < duration:
        frame = cam.get_frame()
        if frame is not None:
            out.write(frame)
        time.sleep(0.05)
    
    out.release()
    return f"Video saved to {filepath}"

def recall_vision():
    """Recalls what was seen recently in the camera."""
    history = _vision_state.get("history", [])
    if not history:
        return "I haven't recorded any visual history yet, sir."
    
    events = []
    # Get last 10 unique events
    seen = set()
    for ts, summary in reversed(history):
        if summary not in seen:
            events.append(f"At {ts.strftime('%H:%M:%S')}: {summary}")
            seen.add(summary)
        if len(events) >= 10: break
    
    return "Recent visual history:\n" + "\n".join(reversed(events))

def get_latest_gesture():
    """Returns the latest raw gesture data."""
    return _vision_state.get("latest_gesture", {"success": False, "gesture": "None"})
