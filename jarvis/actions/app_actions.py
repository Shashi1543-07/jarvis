import os
import pyautogui
import time
import pygetwindow as gw

def open_app(app_name, **kwargs):
    """Open an application using robust system calls or fallback to Windows key method"""
    # Clean app name name
    clean_name = app_name.strip().rstrip('.').lower()
    print(f"Opening app: {clean_name}")
    
    # 1. Broad mapping for system-level apps/commands
    system_map = {
        "camera": "INTERNAL_VISION",
        "your eyes": "INTERNAL_DEEP_SCAN",
        "eyes": "INTERNAL_DEEP_SCAN",
        "calculator": "calc.exe",
        "notepad": "notepad.exe",
        "chrome": "chrome.exe",
        "settings": "start ms-settings:",
        "explorer": "explorer.exe",
        "terminal": "wt.exe",
        "windows camera": "start microsoft.windows.camera:"
    }
    
    if clean_name in system_map:
        cmd = system_map[clean_name]
        
        # Internal Redirects
        if cmd.startswith("INTERNAL"):
            try:
                # Lazy import to avoid circular dependency
                from . import vision_actions
                if cmd == "INTERNAL_VISION":
                    return vision_actions.open_camera()
                elif cmd == "INTERNAL_DEEP_SCAN":
                    return vision_actions.deep_scan()
            except Exception as e:
                print(f"Error triggering internal vision: {e}")
                # Fallback to windows camera app if internal fails
                cmd = "start microsoft.windows.camera:"

        try:
            import subprocess
            subprocess.Popen(cmd, shell=True)
            return f"Opening {clean_name} via system command."
        except Exception as e:
            print(f"Error opening mapped app {clean_name}: {e}")

    # 2. Fallback to Search/Type method (risky with pyautogui fail-safe)
    print(f"Falling back to GUI automation for: {clean_name}")
    try:
        # Avoid crashing everything if mouse is in corner
        original_failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False 
        
        pyautogui.press("win")
        time.sleep(0.5)
        pyautogui.write(clean_name)
        time.sleep(0.5)
        pyautogui.press("enter")
        
        pyautogui.FAILSAFE = original_failsafe
        return f"Attempted to open {clean_name} via GUI automation."
    except Exception as e:
        return f"Failed to open {clean_name} via GUI automation: {e}"

def close_app(app_name, **kwargs):
    """Close an application by name"""
    # Clean app name
    clean_name = app_name.lower().strip().rstrip('.')
    print(f"Closing app: {clean_name}")
    
    # Common process name mapping
    process_map = {
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",  # Fixed mapping
        "firefox": "firefox.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "vlc": "vlc.exe",
        "spotify": "spotify.exe",
        "code": "Code.exe",
        "vscode": "Code.exe",
        "vs code": "Code.exe",          # Added mapping
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
    # Using original clean_name for title search, as titles keep spaces
    try:
        windows = gw.getWindowsWithTitle(clean_name)
        if windows:
            for window in windows:
                try:
                    window.close()
                    print(f"Closed window: {window.title}")
                except:
                    pass
            time.sleep(1) # Wait for close
            
            # Check if still open, if so, fall through to taskkill
            if not gw.getWindowsWithTitle(clean_name):
                return f"Closed {clean_name} windows."
    except Exception as e:
        print(f"Window close error: {e}")

    # 2. Try closing by process name (force close)
    # Be more aggressive with mapping and normalization
    lookup_name = clean_name.replace(" ", "").replace(".", "")
    process_name = process_map.get(clean_name) or process_map.get(lookup_name)
    
    # If not in map, try using the app name as process name
    if not process_name:
        process_name = lookup_name + ".exe"
    
    # Double check for double extension
    if process_name.endswith("..exe"):
        process_name = process_name.replace("..exe", ".exe")
    
    print(f"Attempting taskkill for {process_name}...")
    try:
        result = os.system(f"taskkill /f /im {process_name}")
        if result == 0:
            return f"Successfully closed {clean_name} (process {process_name})."
        else:
            # If exact match failed, try to find process containing the name
            # This is a bit risky but effective for things like "discord" -> "Discord.exe"
            return f"Could not close {clean_name}. Process not found or access denied."
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
