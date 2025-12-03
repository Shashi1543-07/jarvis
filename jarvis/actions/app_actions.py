import os
import pyautogui
import time
import pygetwindow as gw

def open_app(app_name):
    print(f"Opening app: {app_name}")
    pyautogui.press("win")
    time.sleep(0.5)
    pyautogui.write(app_name)
    time.sleep(0.5)
    pyautogui.press("enter")
    return f"Opening {app_name}"

def close_app(app_name):
    print(f"Closing app: {app_name}")
    
    # Common process name mapping
    process_map = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "vlc": "vlc.exe",
        "spotify": "spotify.exe",
        "code": "Code.exe",
        "vscode": "Code.exe",
        "visual studio code": "Code.exe",
        "word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
        "powerpoint": "POWERPNT.EXE",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "edge": "msedge.exe",
        "microsoft edge": "msedge.exe"
    }
    
    # 1. Try closing by window title first (gentle close)
    try:
        windows = gw.getWindowsWithTitle(app_name)
        if windows:
            for window in windows:
                try:
                    window.close()
                    print(f"Closed window: {window.title}")
                except:
                    pass
            time.sleep(1) # Wait for close
            
            # Check if still open, if so, fall through to taskkill
            if not gw.getWindowsWithTitle(app_name):
                return f"Closed {app_name} windows."
    except Exception as e:
        print(f"Window close error: {e}")

    # 2. Try closing by process name (force close)
    process_name = process_map.get(app_name.lower())
    
    # If not in map, try using the app name as process name
    if not process_name:
        # Simple heuristic: remove spaces, add .exe
        process_name = app_name.lower().replace(" ", "") + ".exe"
    
    print(f"Attempting taskkill for {process_name}...")
    try:
        result = os.system(f"taskkill /f /im {process_name}")
        if result == 0:
            return f"Successfully closed {app_name} (process {process_name})."
        else:
            # If exact match failed, try to find process containing the name
            # This is a bit risky but effective for things like "discord" -> "Discord.exe"
            return f"Could not close {app_name}. Process not found or access denied."
    except Exception as e:
        return f"Error closing app via taskkill: {e}"

def switch_window(app_name):
    print(f"Switching to: {app_name}")
    try:
        windows = gw.getWindowsWithTitle(app_name)
        if windows:
            window = windows[0]
            window.activate()
            return f"Switched to {app_name}"
        else:
            return f"Window {app_name} not found."
    except Exception as e:
        return f"Error switching window: {e}"

def minimize_window():
    print("Minimizing current window...")
    try:
        window = gw.getActiveWindow()
        if window:
            window.minimize()
            return "Window minimized."
    except Exception as e:
        return f"Error minimizing window: {e}"

def maximize_window():
    print("Maximizing current window...")
    try:
        window = gw.getActiveWindow()
        if window:
            window.maximize()
            return "Window maximized."
    except Exception as e:
        return f"Error maximizing window: {e}"
