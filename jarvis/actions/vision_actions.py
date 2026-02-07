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
from core.vision.vision_manager import get_vision_manager

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
_tracker = None

# Global vision thread state
_vision_state = {
    "active_modes": set(),  # e.g., {'object_detection', 'face_recognition'}
    "thread": None,
    "running": False,
    "lock": threading.Lock(),
    "current_frame": None,  # Store latest frame for queries
    "latest_summary": "Vision system ready.",
    "latest_gesture": {"success": False, "gesture": "None"},
    "last_update_time": 0,
    "history": [], # List of (timestamp, summary) tuples
    "object_stability": {}, # {obj_name: count} tracking
    "stability_threshold": 3, # Frames required to confirm
    "tracking_roi": None,
    "tracking_object_name": None
}

# State for proactive face learning
_face_learning_state = {
    "last_request_time": 0,
    "pending_name": False,
    "current_unknown_face": None, # Stored frame for learning
    "cooldown": 300, # 5 minutes cooldown between "who are you" requests
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
    Turn on webcam with live feed using Intelligent Vision Manager.
    
    Returns:
        str: Status message with camera type
    """
    vm = get_vision_manager()
    print("Requesting Vision Access...")
    
    # Attempt to open vision (this handles priority selection)
    result = vm.open_vision()
    
    if result["success"]:
        # Start the thread if not already running
        _start_vision_thread()
        
        cam_type = "external" if "external" in result.get("camera_type", "") else "internal"
        
        return {
            "success": True,
            "message": f"Using {cam_type} vision module.",
            "type": "camera_status",
            "is_active": True,
            "camera_type": cam_type,
            "index": result.get("index", 0)
        }
    
    return {
        "success": False, 
        "message": "I don't have access to any visual sensors right now.",
        "type": "camera_status",
        "is_active": False
    }

def close_camera(**kwargs):
    """
    Release webcam and stop vision thread
    
    Returns:
        str: Status message
    """
    print("Closing camera...")
    _vision_state["running"] = False
    _vision_state["active_modes"].clear()
    
    if _vision_state["thread"]:
        # Don't join with timeout if called from within thread (avoid deadlock)
        if threading.current_thread() != _vision_state["thread"]:
            _vision_state["thread"].join(timeout=2)
        _vision_state["thread"] = None
    
    # Force close camera via Vision Manager
    vm = get_vision_manager()
    vm.close_vision()
    
    cv2.destroyAllWindows()
    print("VisionManager: Camera resources fully released.")
    
    return {
        "success": True,
        "message": "Camera closed, sir. My eyes are shut.",
        "type": "camera_status",
        "is_active": False
    }

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

def _smart_vision_route(prompt, original_intent):
    """
    Heuristic to fix common LLM misclassifications for Vision.
    Redirects 'Can you see...' -> Object Detection + Description.
    """
    prompt_lower = prompt.lower()
    
    # SANITIZE HALLUCINATIONS: "Read the book header" is a known hallucination from bad examples.
    if "book header" in prompt_lower or "header" in prompt_lower and len(prompt_lower) < 25:
        print(f"SmartRoute: Sanitizing hallucinated prompt info: '{prompt}'")
        prompt = "General scene analysis"
        prompt_lower = prompt.lower()

    # PROBLEM 1 FIX: "Can you see?" or "Can you even see?" check.
    patterns = ["can you see", "is there a", "do you see", "are there", "can you even see"]
    if any(pattern in prompt_lower for pattern in patterns):
        # Unless they specifically asked for text
        if not any(verify in prompt_lower for verify in ["read", "what is written", "ocr"]):
             print(f"SmartRoute: Providing comprehensive visibility check for '{prompt}'")
             frame = _get_current_frame()
             if frame is None: return {"error": "Camera not active."}
             
             detector = _get_yolo_detector()
             descriptor = _get_scene_descriptor()
             
             yolo_results = detector.detect(frame)
             scene_results = descriptor.describe(frame)
             
             # Format a combined message
             main_desc = scene_results.get('description', "I'm looking at the scene.")
             obj_list = yolo_results.get('objects', [])
             obj_count = len(obj_list)
             
             # Cleanup if one-shot
             if not _vision_state["running"]:
                 get_camera().close_camera()
             
             message = f"Yes, I can see. {main_desc}"
             if obj_count > 0:
                 message += f" I can detect {obj_count} objects including {', '.join(obj_list[:3])}."
             
             return {
                 "type": "visibility_check",
                 "objects": obj_list,
                 "description": main_desc,
                 "message": message
             }
             
    return None

def analyze_scene(prompt="What do you see?", **kwargs):
    """
    General purpose analysis using Vision AI.
    """
    # 0. Robust Prompt Extraction (handle various slot names from LLM)
    if not prompt or prompt == "What do you see?":
        prompt = kwargs.get('prompt') or kwargs.get('content') or kwargs.get('query') or "What do you see?"
    
    # If the prompt is still just the default or very short, treat as generic
    if not prompt or len(prompt) < 3 or "book header" in prompt.lower():
        prompt = "Describe what you see in front of you."

    prompt_lower = prompt.lower()
    
    # Check Smart Route First
    redirect = _smart_vision_route(prompt, "ANALYZE_SCENE")
    if redirect: return redirect

    # 1. Check if this is a SCREEN request
    if "screen" in prompt_lower:
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

            # Use OCREngine for screen content
            try:
                engine = _get_ocr_engine()
                results = engine.detect_and_read(screenshot_cv)
                extracted_text = " ".join([item['detected_text'] for item in results if item['detected_text'].strip()])
                
                return {
                    "text": extracted_text[:1000], 
                    "screenshot_path": filepath,
                    "type": "screen_analysis",
                    "message": f"Screen analysis complete. I found the following text: {extracted_text[:200]}"
                }
            except Exception as e:
                return {"error": f"OCR failed during screen analysis: {e}"}

        except Exception as e:
            return {"error": str(e)}

    # 2. Otherwise its a CAMERA request (Scene/Objects/People)
    else:
        # Determine intent from prompt
        if "read" in prompt_lower or "text" in prompt_lower or "written" in prompt_lower:
            return read_text(prompt, **kwargs)
            
        elif "object" in prompt_lower or "detect" in prompt_lower:
            frame = _get_current_frame()
            if frame is None: return {"error": "Camera not active."}
            detector = _get_yolo_detector()
            return detector.detect(frame)
            
        elif "people" in prompt_lower or "who" in prompt_lower:
            frame = _get_current_frame()
            if frame is None: return {"error": "Camera not active."}
            face_mgr = _get_face_manager()
            results = face_mgr.recognize_faces(frame)
            
            people_details = []
            names = []
            
            for r in results:
                name = r['name']
                names.append(name)
                
                if name != "Unknown":
                    # Fetch from EnhancedMemory if available
                    from core.enhanced_memory import EnhancedMemory
                    mem = EnhancedMemory()
                    
                    details = ""
                    
                    # 1. Check if this is the USER (Fuzzy match with full_name and preferred_names)
                    user_info = mem.long_term.get('user_info', {})
                    is_user = False
                    full_name = user_info.get('full_name', '').lower()
                    pref_names = [n.lower() for n in user_info.get('preferred_names', [])]
                    
                    name_lower = name.lower()
                    if name_lower in full_name or any(pn in name_lower or name_lower in pn for pn in pref_names):
                        is_user = True
                    
                    if is_user:
                        details = "who is my creator and the user I serve"
                        education = user_info.get('education')
                        if education:
                            details += f" ({education})"
                    else:
                        # 2. Check for known relationships
                        rel = mem.relationships.get(name)
                        if not rel:
                            # Try fuzzy match in relationships
                            for r_name, r_data in mem.relationships.items():
                                if name_lower in r_name.lower() or r_name.lower() in name_lower:
                                    rel = r_data
                                    break
                                    
                        if rel:
                            details = f"who is my {rel['type']}"
                            if rel.get('details'):
                                details += f" ({rel['details']})"
                    
                    # 3. Check semantic facts if no user/rel info or to add more
                    facts = mem.semantic_memory.get(name.lower(), [])
                    if facts:
                        top_fact = facts[0]['fact']
                        if details: details += ", and "
                        details += f"I remember: {top_fact}"
                    
                    people_details.append(f"{name} {details}".strip())
                else:
                    people_details.append("an unknown person")
            
            if not names:
                msg = "I don't see anyone in front of me right now."
            else:
                msg = f"I see {', '.join(people_details)}."
                
            return {
                "type": "identify_people",
                "message": msg,
                "people": names,
                "details": people_details
            }

        # DEFAULT: Generic Scene Description + Potential Auto-OCR
        # Determine if we should auto-close (only if vision thread is NOT running)
        should_release = not _vision_state["running"]
        frame = _get_current_frame(auto_close=False) # Get frame but don't close yet
        
        if frame is None: return {"error": "Camera not active."}
        
        # YOLO first to see if we should trigger OCR
        detector = _get_yolo_detector()
        yolo_results = detector.detect(frame)
        objects = yolo_results.get('objects', [])
        
        # If we see a "book", "cell phone", "laptop", or "bottle" -> Trigger OCR automatically!
        text_containers = ["book", "cell phone", "laptop", "bottle", "keyboard", "clock"]
        has_text_container = any(obj in text_containers for obj in objects)
        
        ocr_result = None
        if has_text_container:
            print(f"Auto-OCR: Detected text-carrying object ({objects}), running OCR...")
            ocr_result = read_text(prompt="Generic Scan", **kwargs)

        # Final Scene Descriptor
        descriptor = _get_scene_descriptor()
        scene_result = descriptor.describe(frame)
        
        # Combine
        combined_data = {
            "type": "complex_scene_analysis",
            "description": scene_result.get('description', ""),
            "objects": objects,
            "ocr": ocr_result.get('text') if ocr_result and isinstance(ocr_result, dict) else None
        }
        
        message = scene_result.get('description', "I'm looking at the scene.")
        if ocr_result and isinstance(ocr_result, dict) and ocr_result.get('text'):
             message += f" I also noticed some text: '{ocr_result.get('text')}'."
        
        combined_data["message"] = message
        
        # CLEANUP: Release camera if we opened it just for this and no thread is running
        if should_release:
            get_camera().close_camera()
            
        return combined_data

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
    
    # Cleanup if one-shot
    if not _vision_state["running"]:
        get_camera().close_camera()
        
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

def finalize_face_learning(name, **kwargs):
    """
    Finalize the proactive face learning process once a name is provided.
    """
    global _face_learning_state
    
    if not _face_learning_state["pending_name"] or _face_learning_state["current_unknown_face"] is None:
        return {"error": "No pending face learning request found."}
    
    frame = _face_learning_state["current_unknown_face"]
    face_mgr = _get_face_manager()
    
    print(f"Vision: Finalizing learning for {name}...")
    result = face_mgr.learn_face(frame, name)
    
    if result.get("success"):
        _face_learning_state["pending_name"] = False
        _face_learning_state["current_unknown_face"] = None
        # Don't reset last_request_time to keep the cooldown active
        
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

def get_scene_context(**kwargs):
    """
    Advanced semantic scene understanding.
    Fuses object detection, BLIP, and heuristics.
    """
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active."}
    
    detector = _get_yolo_detector()
    descriptor = _get_scene_descriptor()
    
    # 1. Get objects
    yolo_res = detector.detect(frame)
    objects = yolo_res.get('objects', [])
    
    # 2. Get fused context
    context = descriptor.get_semantic_context(frame, objects)
    
    print(f"Vision: Semantic Context - {context['scene_type']}")
    return context

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

# Already handled by top analyze_scene

def read_text(prompt="Read the text.", **kwargs):
    """
    Robust OCR using the new OCREngine.
    Pauses other vision tasks to ensure full resource availability for OCR.
    """
    # 1. Manage Vision State (Pause Conflicts)
    previous_modes = _vision_state["active_modes"].copy()
    if "object_detection" in _vision_state["active_modes"]:
        _vision_state["active_modes"].remove("object_detection")
        
    print("OCR: Pausing other vision modes for dedicated Text Analysis...")
    time.sleep(0.5) 

    try:
        vm = get_vision_manager()
        
        # 2. Capture Stable Frame
        print("OCR: Capturing stable frame for text...")
        frame = vm.get_stable_frame(sample_count=4) # Reduced from 8 for faster response
        
        if frame is None:
            _vision_state["active_modes"] = previous_modes
            return {"error": "Camera not active."}

        # 3. Process
        engine = _get_ocr_engine()
        if not engine._easyocr_available and not engine._tesseract_available:
             _vision_state["active_modes"] = previous_modes
             return {
                 "error": "OCR Core missing.",
                 "message": "I cannot read text because my OCR engines (EasyOCR/Tesseract) are not properly installed. Please ask me to 'repair vision cores' to fix this.",
                 "type": "error"
             }
             
        results = engine.detect_and_read(frame)
        
        # 4. Filter & Confidence Check (Max Sensitivity: 0.25)
        valid_texts = []
        for item in results:
            # More permissive threshold (0.25 instead of 0.35)
            if item.get('confidence', 0) > 0.25 and len(item.get('detected_text', '')) >= 1:
                valid_texts.append(item['detected_text'])
                
        extracted_text = " ".join(valid_texts)

        # Restore state
        _vision_state["active_modes"] = previous_modes

        if extracted_text.strip():
            return {
                "text": extracted_text, 
                "details": results,
                "message": f"I read: {extracted_text}",
                "type": "ocr_result"
            }
        elif len(results) > 0: 
            # We found text but it was low confidence
            msg = "I detect some text, but it's too blurry or faint to read. Please improve the lighting, hold the paper steadier, or bring it slightly closer to the lens."
            return {
                "text": "Unclear text.", 
                "message": msg,
                "type": "ocr_result_low_conf"
            }
        else:
            return {
                "text": "No text detected.",
                "message": "I don't see any readable text. Try aligning the paper with the center of my vision and ensuring good lighting.",
                "type": "ocr_result"
            }
    except Exception as e:
        _vision_state["active_modes"] = previous_modes
        print(f"OCR Critical Failure: {e}")
        return {"error": f"OCR Engine failed: {str(e)}"}

def repair_vision_system(**kwargs):
    """
    Force reset and re-initialization of all vision engines.
    Use this when Jarvis says he can't read but the camera is physically working.
    """
    global _ocr_engine, _yolo_detector, _scene_descriptor, _face_manager
    
    print("VISION REPAIR: Wiping engine instances and re-initializing environment...")
    _ocr_engine = None
    _yolo_detector = None
    _scene_descriptor = None
    _face_manager = None
    
    # Re-initialize OCR
    try:
        engine = _get_ocr_engine()
        if engine._easyocr_available:
            msg = "Vision Cores re-initialized successfully. I can see clearly now."
        else:
            msg = "Vision Cores reset, but the underlying libraries (EasyOCR/Tesseract) still fail to load. Please check your console for errors."
            
        return {
            "success": engine._easyocr_available,
            "message": msg,
            "type": "vision_repair"
        }
    except Exception as e:
        return {"error": str(e), "message": f"Repair failed: {e}"}

def recall_vision_memory(query=None, **kwargs):
    """
    Recall text or objects seen recently.
    
    Args:
        query: Optional text to filter memory (e.g. "recipe", "password")
    """
    engine = _get_ocr_engine()
    mem_results = engine.recall_recent(query)
    
    if not mem_results:
        return "I haven't seen any text matching that recently."
    
    # Format the most recent one
    top = mem_results[0]
    ago = int(time.time() - top['timestamp'])
    
    return f"I remember seeing '{top['text']}' about {ago} seconds ago."

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
        
        # Use new engine even for legacy call
        engine = _get_ocr_engine()
        results = engine.detect_and_read(frame)
        text = " ".join([r['detected_text'] for r in results])
        return f"Extracted text: {text}"
    else:
        if os.path.exists(image_path):
            img = cv2.imread(image_path)
            engine = _get_ocr_engine()
            results = engine.detect_and_read(img)
            text = " ".join([r['detected_text'] for r in results])
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
        # Add motion detection if available in the loop
        _vision_state["active_modes"].add("motion_detection")
    _start_vision_thread()
    return "Initialising deep scan. All vision systems are now active and tracking, sir."

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
    _vision_state["active_modes"].add("posture_guard")
    return "Posture monitoring enabled. Sit up straight!"

# ============================================================================
# VISION LOOP & HELPERS
# ============================================================================

def _get_current_frame(auto_close=False):
    """
    Get latest frame from camera.
    
    Args:
        auto_close: If True and we opened the camera just for this call, close it after.
                    (Note: Use with caution as multiple calls might need it open).
    """
    cam = get_camera()
    
    # If vision thread running, use cached frame
    if _vision_state["running"] and _vision_state["current_frame"] is not None:
        return _vision_state["current_frame"]
    
    # If not running, we must open for one-shot
    opened_now = False
    if not cam.is_active:
        if not cam.open_camera():
            return None
        opened_now = True
        # If we just opened it, give it a moment for auto-exposure
        time.sleep(0.5)
    
    frame = cam.get_frame()
    
    if opened_now and auto_close:
        cam.close_camera()
        
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
            # Check if we should stop even if frame is none (to prevent hung thread)
            if not _vision_state["running"]: break
            time.sleep(0.05)
            continue
        
        # Cache frame for queries
        _vision_state["current_frame"] = frame.copy()
        
        display_frame = frame.copy()
        modes = _vision_state["active_modes"].copy()
        
        # Object Detection & Summary
        if yolo is None:
            yolo = _get_yolo_detector()
        
        detect_res = yolo.detect(frame)
        current_objects = set(detect_res.get('objects', []))
        
        # Temporal Stability Filtering
        stable_objects = []
        for obj in current_objects:
            _vision_state["object_stability"][obj] = _vision_state["object_stability"].get(obj, 0) + 1
            if _vision_state["object_stability"][obj] >= _vision_state["stability_threshold"]:
                stable_objects.append(obj)
        
        # Cleanup stability for missing objects
        for obj in list(_vision_state["object_stability"].keys()):
            if obj not in current_objects:
                _vision_state["object_stability"][obj] -= 1
                if _vision_state["object_stability"][obj] <= 0:
                    del _vision_state["object_stability"][obj]

        if stable_objects:
            from collections import Counter
            counts = Counter(stable_objects)
            summary = ", ".join([f"{v} {k}" for k, v in counts.items()])
            
            # Periodic semantic summary (every 10s)
            now = time.time()
            if now - _vision_state["last_update_time"] > 10:
                descriptor = _get_scene_descriptor()
                context = descriptor.get_semantic_context(frame, stable_objects)
                
                # Deep Verification: If a "cat" or "dog" is detected but confidence is on edge, verify with BLIP
                if "cat" in stable_objects or "dog" in stable_objects:
                    vqa = descriptor.answer_question(frame, "Is there a cat or dog here?")
                    if "no" in vqa['answer'].lower():
                        print(f"Vision: Deep Verification filtered out false positive.")
                        _vision_state["latest_summary"] = "I'm not entirely sure, but I see shapes that look like objects."
                    else:
                        _vision_state["latest_summary"] = context['summary']
                else:
                    _vision_state["latest_summary"] = context['summary']
                
                _vision_state["history"].append((datetime.datetime.now(), _vision_state["latest_summary"]))
                if len(_vision_state["history"]) > 50: _vision_state["history"].pop(0)
                _vision_state["last_update_time"] = now
            else:
                _vision_state["latest_summary"] = f"Visible: {summary}"
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
                
                # Proactive Learning Check
                if name == "Unknown" and result['quality']['is_good']:
                    now = time.time()
                    if now - _face_learning_state["last_request_time"] > _face_learning_state["cooldown"] and not _face_learning_state["pending_name"]:
                         print(f"Vision: Detected high-quality unknown face. Quality: {result['quality']['sharpness']:.1f}")
                         _vision_state["latest_summary"] = "I see an unknown person with clear visibility. I should ask for their name to remember them."
                         _face_learning_state["current_unknown_face"] = frame.copy()
                         _face_learning_state["pending_name"] = True
                         _face_learning_state["last_request_time"] = now
        
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
        
        # QR Scanning
        if "qr_scanning" in modes:
            if qr_decode is not None:
                decoded_objects = qr_decode(frame)
                for obj in decoded_objects:
                    data = obj.data.decode('utf-8')
                    (x, y, w, h) = obj.rect
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(display_frame, f"QR: {data}", (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                    _vision_state["latest_summary"] = f"Detected QR code: {data}"

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
        
        # Object Tracking
        if "object_tracking" in modes:
            if _tracker is not None:
                success, bbox = _tracker.update(frame)
                if success:
                    _vision_state["tracking_roi"] = bbox
                    (x, y, w, h) = [int(v) for v in bbox]
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
                    cv2.putText(display_frame, f"TRACKING: {_vision_state.get('tracking_object_name', 'OBJECT')}", 
                               (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                else:
                    _vision_state["active_modes"].discard("object_tracking")
                    _vision_state["latest_summary"] = f"Lost track of {_vision_state.get('tracking_object_name', 'object')}."
        
        # Show frame
        cv2.imshow("Jarvis Vision", display_frame)
        
        # Handle window close or 'q' press
        try:
            if cv2.getWindowProperty("Jarvis Vision", cv2.WND_PROP_VISIBLE) < 1:
                _vision_state["running"] = False
                break
        except:
            # Window might already be destroyed
            pass
            
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            _vision_state["running"] = False
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

def object_tracking(object_name=None):
    """
    Initialize object tracking. Uses YOLO to find the object first, then starts a CSRT tracker.
    """
    global _tracker
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active."}
        
    if not object_name:
        return {"message": "Please specify what you want me to track, sir.", "type": "input_required"}
        
    print(f"Vision: Attempting to track {object_name}...")
    
    # 1. Use YOLO to find the object ROI
    detector = _get_yolo_detector()
    results = detector.detect(frame)
    details = results.get('details', [])
    
    roi = None
    for d in details:
        if object_name.lower() in d['label'].lower():
            roi = d['box'] # [l, t, r, b]
            break
            
    if roi is None:
        return {"message": f"I can't see a {object_name} right now to start tracking.", "type": "error"}
        
    # 2. Initialize Tracker (CSRT is robust)
    try:
        if not hasattr(cv2, 'TrackerCSRT_create'):
             return {"error": "OpenCV CSRT Tracker not available in this version."}
             
        _tracker = cv2.TrackerCSRT_create()
        # Convert [l, t, r, b] to (x, y, w, h)
        l, t, r, b = roi
        bbox = (int(l), int(t), int(r-l), int(b-t))
        _tracker.init(frame, bbox)
        
        with _vision_state["lock"]:
            _vision_state["tracking_roi"] = bbox
            _vision_state["tracking_object_name"] = object_name
            _vision_state["active_modes"].add("object_tracking")
            
        _start_vision_thread()
        return f"Tracking {object_name} initialized. My sensors are locked on, sir."
    except Exception as e:
        return {"error": f"Failed to initialize tracker: {e}"}

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
    """
    Advanced document scanning: Perspective correction + OCR.
    """
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active."}
    
    # 1. Perspective correction (attempt to find document contour)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 75, 200)
    
    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
    
    doc_cnt = None
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            doc_cnt = approx
            break
            
    processed_frame = frame
    if doc_cnt is not None:
        # Simple perspective transform helper logic inline or as separate function
        def order_points(pts):
            rect = np.zeros((4, 2), dtype="float32")
            s = pts.sum(axis=1)
            rect[0] = pts[np.argmin(s)]
            rect[2] = pts[np.argmax(s)]
            diff = np.diff(pts, axis=1)
            rect[1] = pts[np.argmin(diff)]
            rect[3] = pts[np.argmax(diff)]
            return rect

        def four_point_transform(image, pts):
            rect = order_points(pts)
            (tl, tr, br, bl) = rect
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
            M = cv2.getPerspectiveTransform(rect, dst)
            return cv2.warpPerspective(image, M, (maxWidth, maxHeight))

        pts = doc_cnt.reshape(4, 2)
        processed_frame = four_point_transform(frame, pts)
        print("Vision: Document contour found and perspective corrected.")
    
    # 2. Run OCR on the processed (possibly warped) frame
    engine = _get_ocr_engine()
    results = engine.detect_and_read(processed_frame)
    text = " ".join([r['detected_text'] for r in results if r.get('confidence', 0) > 0.3])
    
    if not text.strip():
        return {"message": "I found a document structure but couldn't read the text clearly. Please hold it steady.", "type": "ocr_failed"}
        
    return {
        "text": text,
        "type": "document_scan",
        "message": f"Document scanned. Here's what I read: {text[:500]}..."
    }

def highlight_object(object_name=None):
    """
    Finds and highlights an object in the live view.
    """
    if not object_name:
        return {"message": "What should I highlight, sir?", "type": "input_required"}
        
    _start_vision_thread()
    _vision_state["active_modes"].add("object_detection")
    # We'll use the latest_summary to indicate we are looking for it
    _vision_state["latest_summary"] = f"Looking for {object_name} to highlight..."
    return f"Scanning for {object_name}. I'll highlight it as soon as it's in range."

def activity_recognition():
    """
    Activity recognition using pose estimation.
    """
    if mp is None:
        return "MediaPipe not installed."
        
    frame = _get_current_frame()
    if frame is None:
        return {"error": "Camera not active."}
        
    poses = _get_pose_guard()
    res = poses.check_posture(frame)
    
    if not res["success"]:
        return {"message": "I can't see your full body to recognize activity.", "type": "error"}
        
    # Heuristic based on landmarks (simple standing vs sitting)
    # Using normalized Y coordinates of shoulders vs hips
    landmarks = res["landmarks"]
    # mp_pose.PoseLandmark.LEFT_HIP = 23, LEFT_SHOULDER = 11
    # If using Mediapipe directly inside pose_guard
    try:
        # This is a bit internal to pose_guard's implementation
        shoulder_y = landmarks[11].y if hasattr(landmarks[11], 'y') else 0.5
        hip_y = landmarks[23].y if hasattr(landmarks[23], 'y') else 0.7
        
        diff = hip_y - shoulder_y
        if diff < 0.2:
            activity = "SITTING"
        else:
            activity = "STANDING"
            
        return {
            "activity": activity,
            "message": f"I see you are currently {activity.lower()}.",
            "type": "activity_recognition"
        }
    except:
        return {"message": "I see you there, but I'm still analyzing your movement.", "type": "activity_summary"}

def record_video(duration=10, filename=None):
    """Record video clip"""
    try:
        duration = int(duration)
    except:
        duration = 10
        
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
    gesture = _vision_state.get("latest_gesture")
    if gesture is None:
        return {"success": False, "gesture": "None"}
    return gesture
