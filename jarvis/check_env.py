import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Version: {sys.version}")
print("Sys Path:")
for p in sys.path:
    print(f"  {p}")

print("\nAttempting to import webrtcvad...")
try:
    import webrtcvad
    print(f"Success! webrtcvad file: {webrtcvad.__file__}")
except ImportError as e:
    print(f"Failed to import webrtcvad: {e}")

print("\nAttempting to import _webrtcvad (C extension)...")
try:
    import _webrtcvad
    print("Success importing _webrtcvad")
except ImportError as e:
    print(f"Failed to import _webrtcvad: {e}")

try:
    import pip
    print(f"\npip version: {pip.__version__}")
except:
    pass
