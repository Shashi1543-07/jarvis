import sys
import os
import time
import subprocess

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'jarvis'))

from jarvis.core.router import Router

def test_window_management():
    print("--- Testing Window Management ---")
    router = Router()
    
    # 1. Open two test applications
    print("\nOpening test applications (Notepad and Calculator)...")
    subprocess.Popen("notepad.exe")
    subprocess.Popen("calc.exe")
    time.sleep(3) # Wait for them to open

    # 2. List windows
    print("\nRequesting window list...")
    text_list = "Jarvis, list open windows."
    res = router.route(text_list)
    print(f"Jarvis: {res['text']}")

    # 3. Test Tiling (Split Screen)
    print("\nTesting split screen...")
    text_split = "Jarvis, split screen between notepad and calculator."
    res = router.route(text_split)
    print(f"Jarvis: {res['text']}")
    
    time.sleep(2)
    
    # 4. Test Maximize
    print("\nTesting maximize...")
    text_max = "Jarvis, maximize notepad."
    res = router.route(text_max)
    print(f"Jarvis: {res['text']}")

    print("\nWindow management test complete. You should see Notepad and Calculator positioned and scaled.")

if __name__ == "__main__":
    test_window_management()
