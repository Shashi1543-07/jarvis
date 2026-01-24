import pyautogui
import time

def type_text(text):
    print(f"Typing: {text}")
    pyautogui.write(text, interval=0.05)
    return f"Typed: {text}"

def press_key(key):
    print(f"Pressing key: {key}")
    pyautogui.press(key)
    return f"Pressed {key}"

def hotkey(keys):
    # keys should be a list or comma-separated string
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.split(',')]
    print(f"Pressing hotkey: {keys}")
    pyautogui.hotkey(*keys)
    return f"Pressed hotkey {keys}"

def mouse_move(x, y):
    print(f"Moving mouse to {x}, {y}")
    pyautogui.moveTo(x, y)
    return f"Moved mouse to {x}, {y}"

def mouse_click(x=None, y=None, button="left", clicks=1):
    print(f"Clicking mouse at {x}, {y}")
    if x and y:
        pyautogui.click(x=x, y=y, button=button, clicks=clicks)
    else:
        pyautogui.click(button=button, clicks=clicks)
    return "Mouse clicked"

def mouse_scroll(amount):
    print(f"Scrolling {amount}")
    pyautogui.scroll(amount)
    return f"Scrolled {amount}"

def click_on_text(target_text):
    """
    Find specific text on screen and click it.
    """
    print(f"Automation: Searching screen for '{target_text}' to click...")
    try:
        import easyocr
        import numpy as np
        import cv2
        
        # Capture screen
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        
        # OCR
        reader = easyocr.Reader(['en'])
        results = reader.readtext(screenshot_cv)
        
        target_text = target_text.lower()
        best_match = None
        
        for (bbox, text, prob) in results:
            if target_text in text.lower():
                best_match = bbox
                print(f"Found match: '{text}' at {bbox}")
                break
        
        if best_match:
            # bbox is [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            center_x = (best_match[0][0] + best_match[1][0]) // 2
            center_y = (best_match[0][1] + best_match[2][1]) // 2
            
            pyautogui.click(center_x, center_y)
            return f"Clicked on '{target_text}' at ({center_x}, {center_y})"
        
        return f"Could not find text '{target_text}' on screen."
    except Exception as e:
        return f"Automation Error: {e}"

def type_at_text(target_text, text_to_type):
    """Find text, click it, and type."""
    res = click_on_text(target_text)
    if "Clicked" in res:
        time.sleep(0.5)
        type_text(text_to_type)
        pyautogui.press("enter")
        return f"Typed '{text_to_type}' at {target_text}"
    return res
