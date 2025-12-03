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
