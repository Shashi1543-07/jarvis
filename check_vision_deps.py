"""
Quick Dependency Check for Vision System
"""
import sys

print("="*60)
print("JARVIS VISION - Dependency Check")
print("="*60)

print(f"\nPython Version: {sys.version}")
print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

print("\n" + "="*60)
print("Checking CORE Vision Dependencies...")
print("="*60)

core_deps = {
    'OpenCV': 'cv2',
    'NumPy': 'numpy',
    'YOLOv8 (ultralytics)': 'ultralytics',
    'Face Recognition': 'face_recognition',
    'Transformers (BLIP)': 'transformers',
    'PyTorch': 'torch',
    'TorchVision': 'torchvision',
    'Pillow': 'PIL',
    'DeepFace': 'deepface',
    'TF-Keras': 'tf_keras',
    'DuckDuckGo Search': 'duckduckgo_search',
}

installed = []
missing = []

for name, module in core_deps.items():
    try:
        __import__(module)
        print(f"  ✓ {name}")
        installed.append(name)
    except ImportError as e:
        print(f"  ✗ {name} - MISSING")
        missing.append(name)

print("\n" + "="*60)
print("Checking OPTIONAL Dependencies...")
print("="*60)

optional_deps = {
    'MediaPipe (gestures/pose)': 'mediapipe',
    'PyTesseract (OCR)': 'pytesseract',
    'PyzbarUSE (QR scanning)': 'pyzbar',
    'DLib (face encoding)': 'dlib',
}

for name, module in optional_deps.items():
    try:
        __import__(module)
        print(f"  ✓ {name}")
    except ImportError:
        print(f"  ○ {name} - Not installed (optional)")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Core dependencies: {len(installed)}/{len(core_deps)} installed")

if missing:
    print(f"\n⚠ Missing core dependencies:")
    for dep in missing:
        print(f"  - {dep}")
    print("\nRun: pip install -r requirements.txt")
else:
    print("\n✓ All core vision dependencies are installed!")
    print("✓ JARVIS Vision System is ready to use!")

print("\n" + "="*60)
