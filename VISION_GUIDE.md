# JARVIS Vision System - Quick Start Guide

## Installation

1. **Install Dependencies:**
```bash
cd c:\Users\lenovo\JarvisAI
pip install -r requirements.txt
```

This will install:
- `ultralytics` (YOLOv8 - object detection)
- `face-recognition` (Face recognition)
- `transformers` + `torch` (BLIP - scene description)
- `deepface` (Emotion recognition)
- `duckduckgo-search` (Internet search)
- And other dependencies

**Note:** First run will download pre-trained models (~2-3GB). This is normal.

## Setup Face Recognition

1. **Create Faces Directory:**
Already created at: `c:\Users\lenovo\JarvisAI\faces\`

2. **Add Sample Faces:**
- Take clear frontal face photos
- Save as `faces/YourName.jpg`
- Example: `faces/Shashi.jpg`, `faces/Rohan.jpg`

3. **Face encodings will be automatically generated** on first use

## Voice Commands

### Camera Control
- **"Jarvis, open your eyes"** → Opens camera
- **"Close camera"** → Closes camera
- **"Take a photo"** → Captures snapshot

### Object Detection
- **"What do you see?"** → Describes scene using BLIP AI
- **"What objects do you see?"** → Lists detected objects via YOLO
- **"Is there a laptop?"** → Checks for specific object
- **"Count the people"** → Counts specific object type
- **"What is this object?"** → Detects object + searches internet

### Face Recognition
- **"Who is in front of you?"** → Identifies people
- **"Do you see Rohan?"** → Checks for specific person
- **"Remember this face as Shashi"** → Learns new face (permanent)
- **"Is this me?"** → Checks identity

### Scene Understanding
- **"Describe what you see"** → Natural language scene description
- **"What's happening in the room?"** → Scene analysis

### Emotion Recognition
- **"How do I look?"** → Detects your emotion
- **"Are they happy or sad?"** → Analyzes facial expression

### Internet Search
- **"Search about this object"** → Searches for detected object info
- **"Tell me what this is"** → Object detection + web search

## Testing

Run the complete test suite:
```bash
cd c:\Users\lenovo\JarvisAI
python test_vision_complete.py
```

This will test:
- All dependencies
- Vision module imports
- Camera operations
- Object detection
- Face recognition
- Scene description
- Emotion detection
- Internet search

## Face Memory System

Faces are stored in:
- `faces/*.jpg` - Face images
- `faces/face_encodings.pkl` - Cached encodings (auto-generated)

### Learn New Face:
1. **Via Voice:** "Jarvis, remember this face as [Name]"
2. JARVIS will capture your face and save to `faces/[Name].jpg`
3. Face encoding is cached for fast recognition
4. Next time: JARVIS will recognize you by name!

### Persistence:
- Faces are saved to disk
- Encodings are cached
- Memory persists across restarts
- Just keep the faces/ directory

## Architecture

```
jarvis/
├── core/
│   ├── vision/
│   │   ├── face_manager.py       # Face recognition with memory
│   │   ├── yolo_detector.py      # YOLOv8 object detection
│   │   ├── scene_description.py  # BLIP scene captioning
│   │   ├── emotion_detector.py   # DeepFace emotions
│   │   └── internet_search.py    # DuckDuckGo search
│   ├── brain.py                   # Updated with vision commands
│   └── router.py                  # Routes to vision_actions
├── actions/
│   └── vision_actions.py         # 25+ vision functions
└── vision/
    └── utils.py                   # Camera manager

faces/                             # Face database directory
├── YourName.jpg                  # Your face
├── Friend1.jpg
└── face_encodings.pkl            # Auto-generated cache
```

## Features Implemented

✅ **Live Camera Access** - Real-time webcam feed
✅ **Object Detection (YOLO)** - Detect 80+ object types
✅ **Face Recognition** - Identify known people
✅ **Face Learning** - Remember new faces permanently
✅ **Scene Description (BLIP)** - Natural language captions
✅ **Emotion Recognition** - 7 emotions (happy, sad, angry, etc.)
✅ **Internet Search** - Search info about detected objects
✅ **OCR Text Extraction** - Read text from camera
✅ **Motion Detection** - Security mode
✅ **QR/Barcode Scanning** - Read codes
✅ **Gesture Control** - Hand gestures
✅ **Posture Monitoring** - Check sitting posture
✅ **Screen Analysis** - AI vision for screenshots

## Performance

- **YOLOv8n** (nano model) - Fast, optimized for real-time
- **Frame skipping** - Process every 2-3 frames for speed
- **Lazy loading** - Models load only when needed
- **Threaded execution** - Non-blocking vision loop
- **Cached encodings** - Fast face recognition

## Troubleshooting

**Dependencies not installing?**
- Try: `pip install --upgrade pip`
- Install separately: `pip install ultralytics face-recognition transformers torch deepface`

**YOLO model download fails?**
- First run downloads yolov8n.pt automatically
- Requires internet connection
- ~6MB download

**Face recognition slow?**
- Encodings are cached after first scan
- Subsequent runs are much faster

**Camera won't open?**
- Check camera permissions
- Close other apps using camera
- Try camera_id=1 if multiple cameras

## Next Steps

1. Install dependencies
2. Add your face to `faces/`
3. Run test: `python test_vision_complete.py`
4. Start JARVIS: `python jarvis/app.py`
5. Try voice commands!
