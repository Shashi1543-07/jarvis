import pyautogui
import time
import math
import random
import threading
from typing import Optional

# Safety failsafe
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

class InputController:
    """
    Safe wrapper for Mouse and Keyboard control.
    Implements human-like movement and emergency stops.
    """
    def __init__(self):
        self._stop_event = threading.Event()
        
    def stop(self):
        """Emergency stop signal"""
        self._stop_event.set()

    def _check_stop(self):
        if self._stop_event.is_set():
            raise KeyboardInterrupt("InputController: Emergency Stop Triggered")

    def mouse_move(self, x: int, y: int, duration: float = 0.5):
        """Human-like mouse movement with easing"""
        self._check_stop()
        
        start_x, start_y = pyautogui.position()
        dist = math.hypot(x - start_x, y - start_y)
        
        # Adaptive duration if not specified
        if duration is None:
            duration = min(2.0, max(0.2, dist / 1000.0))
            
        # Add slight randomness to path (Bezier curve simple simulation)
        # For strict control we might want linear, but human-like was requested.
        # However, for reliability, stick to pyautogui's easing.
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)

    def mouse_click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", double: bool = False):
        self._check_stop()
        if x is not None and y is not None:
            self.mouse_move(x, y)
            
        clicks = 2 if double else 1
        pyautogui.click(button=button, clicks=clicks)

    def mouse_scroll(self, clicks: int):
        self._check_stop()
        pyautogui.scroll(clicks)

    def keyboard_type(self, text: str, processing_delay: float = 0.05):
        """Type text with varying delay to simulate human typing"""
        self._check_stop()
        
        for char in text:
            self._check_stop()
            pyautogui.write(char)
            # Randomize delay slightly
            time.sleep(random.uniform(processing_delay * 0.5, processing_delay * 1.5))

    def keyboard_press(self, keys: list):
        """Press key combination"""
        self._check_stop()
        # Handle combinations (last key press, others hold)
        if len(keys) > 1:
            with pyautogui.hold(keys[0]):
                for k in keys[1:]:
                    pyautogui.press(k)
        else:
            pyautogui.press(keys[0])

    def get_mouse_position(self):
        return pyautogui.position()
