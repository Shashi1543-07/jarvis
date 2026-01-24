import subprocess
import os
import time
import platform
import pygetwindow as gw
import psutil

class SystemControlManager:
    """
    High-level System and Application control.
    """
    def __init__(self):
        self.os_type = platform.system()

    def open_app(self, app_name: str):
        """Open an application or URL in a non-blocking way"""
        print(f"SystemControl: Opening {app_name}")
        if self.os_type == "Windows":
            # Heuristic map for common apps
            common_map = {
                "chrome": "chrome.exe",
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "explorer": "explorer.exe",
                "cmd": "start cmd",
                "terminal": "wt.exe",
                "youtube": "start https://www.youtube.com",
                "google": "start https://www.google.com"
            }
            
            # 1. Check local map FIRST
            if app_name.lower() in common_map:
                cmd = common_map[app_name.lower()]
                try:
                    subprocess.Popen(cmd, shell=True)
                    time.sleep(1.0) 
                    return True
                except Exception as e:
                    print(f"Error opening mapped app: {e}")
                    return False
            
            # 2. Check if it's a URL
            if app_name.lower().startswith("http") or ("." in app_name and "/" not in app_name and " " not in app_name):
                 # Simple heuristic for domain like 'google.com' but avoid 'file.txt'
                 if not app_name.startswith("http"):
                     app_name = f"https://{app_name}"
                 try:
                    os.system(f"start {app_name}")
                    return True
                 except:
                    pass
            
            # 3. Fallback to generic name
            cmd = app_name
            
            try:
                # Use start to detach process
                subprocess.Popen(cmd, shell=True)
                time.sleep(1.0) # Wait for it to possibly appear
                return True
            except Exception as e:
                print(f"Error opening app: {e}")
                return False
        return False

    def close_app(self, app_name: str):
        """Close application by name"""
        print(f"SystemControl: Closing {app_name}")
        terminated = False
        for proc in psutil.process_iter(['name']):
            if app_name.lower() in proc.info['name'].lower():
                try:
                    proc.terminate()
                    terminated = True
                except Exception as e:
                    print(f"Error terminating process: {e}")
        return terminated

    def get_active_window(self):
        """Get title of active window"""
        try:
            win = gw.getActiveWindow()
            return win.title if win else None
        except:
            return None
            
    def focus_window(self, app_name: str):
        """Bring window to foreground"""
        try:
            windows = gw.getWindowsWithTitle(app_name)
            if windows:
                win = windows[0]
                if not win.isActive:
                    win.activate()
                # Restore if minimized
                if win.isMinimized:
                    win.restore()
                return True
        except Exception as e:
            print(f"Error focusing window: {e}")
        return False

    def system_command(self, cmd: str):
        """Execute system commands like volume, brightness"""
        if cmd == "shutdown":
            # Safety check usually handled by Executor, but double check here
            pass 
        elif cmd == "lock":
            if self.os_type == "Windows":
                os.system("rundll32.exe user32.dll,LockWorkStation")
