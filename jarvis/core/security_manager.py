#!/usr/bin/env python3
"""
Security Manager for Jarvis AI
Implements secret code protection for sensitive operations
"""

import os
import subprocess
import psutil
import re

class SecurityManager:
    def __init__(self):
        self.secret_code = "tronix"
        self.authorized = False
        self.risky_operations = [
            "shutdown", "restart", "sleep", "hibernate", "lock", "logout",
            "delete", "remove", "format", "kill", "terminate", "password",
            "personal", "private", "secret", "confidential", "private info",
            "personal info", "private information", "personal information"
        ]
        self.pending_command = None
    
    def is_risky_operation(self, command):
        """Check if the command is potentially risky"""
        command_lower = command.lower()
        return any(op in command_lower for op in self.risky_operations)
    
    def verify_secret_code(self, user_input):
        """Verify if user provided the correct secret code"""
        return self.secret_code.lower() in user_input.lower()
    
    def authorize_temporarily(self):
        """Temporarily authorize the user after providing correct code"""
        self.authorized = True
    
    def is_authorized(self):
        """Check if user is currently authorized"""
        return self.authorized
    
    def reset_authorization(self):
        """Reset authorization after a period of time or after operation"""
        self.authorized = False

def find_and_launch_app(app_name):
    """
    Dynamically find and launch applications based on user request
    """
    app_name = app_name.lower().strip()

    # Common app name mappings
    app_mappings = {
        'vs code': ['code', 'visual studio code'],
        'visual studio code': ['code', 'visual studio code'],
        'chrome': ['chrome', 'google chrome'],
        'google chrome': ['chrome', 'google chrome'],
        'edge': ['msedge', 'microsoft edge'],
        'microsoft edge': ['msedge', 'microsoft edge'],
        'firefox': ['firefox'],
        'notepad++': ['notepad++', 'notepad plus plus'],
        'explorer': ['explorer', 'file explorer'],
        'file explorer': ['explorer', 'file explorer'],
        'calculator': ['calc', 'calculator'],
        'calc': ['calc', 'calculator'],
        'paint': ['mspaint', 'paint'],
        'word': ['winword', 'microsoft word'],
        'excel': ['excel', 'microsoft excel'],
        'powerpoint': ['powerpnt', 'microsoft powerpoint'],
        'outlook': ['outlook', 'microsoft outlook'],
        'onenote': ['onenote', 'microsoft onenote'],
        'teams': ['teams', 'microsoft teams'],
        'spotify': ['spotify'],
        'vlc': ['vlc'],
        'steam': ['steam'],
        'discord': ['discord'],
        'telegram': ['telegram'],
        'whatsapp': ['whatsapp'],
        'brave': ['brave'],
        'opera': ['opera'],
        'sublime': ['sublime_text', 'sublime'],
        'pycharm': ['pycharm', 'pycharm64'],
        'intellij': ['idea', 'intellij'],
        'atom': ['atom'],
        'slack': ['slack'],
        'zoom': ['zoom'],
        'skype': ['skype'],
    }

    # Try to find the actual executable name
    possible_names = [app_name]
    if app_name in app_mappings:
        possible_names.extend(app_mappings[app_name])

    # First, try to launch using Windows 'start' command (works for UWP apps and registered programs)
    for name in possible_names:
        try:
            # Try with the exact name first
            result = subprocess.run(['start', name], shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return True, f"Launched {name} successfully."
        except:
            pass

        # Try with common executable patterns
        executable_variants = [
            name.replace(' ', ''),
            name.replace(' ', '_'),
            name.replace(' ', '-'),
            name.replace(' ', '').replace('-', ''),
            name.replace(' ', '').replace('_', ''),
        ]

        for variant in executable_variants:
            try:
                result = subprocess.run(['start', variant], shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return True, f"Launched {variant} successfully."
            except:
                pass

    # Search in common installation directories if direct launch failed
    search_paths = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\Users\%USERNAME%\AppData\Local\Programs",
        r"C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs",
    ]

    for name in possible_names:
        for path_template in search_paths:
            path = os.path.expandvars(path_template)
            if os.path.exists(path):
                for root, dirs, files in os.walk(path, topdown=True):
                    # Limit search depth to avoid taking too long
                    if root[len(path):].count(os.sep) > 3:
                        continue
                    for file in files:
                        if file.lower().endswith('.exe'):
                            # Check if the filename contains our app name (case-insensitive)
                            if name.replace(' ', '').replace('_', '').replace('-', '') in \
                               file.replace(' ', '').replace('_', '').replace('-', '').lower():
                                exe_path = os.path.join(root, file)
                                try:
                                    subprocess.Popen(exe_path)
                                    return True, f"Launched {exe_path} successfully."
                                except Exception as e:
                                    print(f"Failed to launch {exe_path}: {e}")
                                    continue

    # If not found in file system, try Windows search with 'where' command
    for name in possible_names:
        try:
            result = subprocess.run(['where', '/R', 'C:\\Program Files', f'*{name.replace(" ", "*")}*.exe'],
                                   capture_output=True, text=True, shell=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                # Get the first match
                exe_paths = result.stdout.strip().split('\n')
                for exe_path in exe_paths:
                    exe_path = exe_path.strip()
                    if exe_path:
                        try:
                            subprocess.Popen(exe_path)
                            return True, f"Launched {exe_path} successfully."
                        except:
                            continue
        except subprocess.TimeoutExpired:
            pass
        except:
            pass

    # If all else fails, try to open as a URI or use Windows search
    try:
        # Try to treat it as a URI (for web apps, store apps, etc.)
        subprocess.run(['start', app_name], shell=True, capture_output=True, text=True)
        return True, f"Attempted to launch {app_name}."
    except:
        pass

    return False, f"Could not find application: {app_name}"

def adjust_brightness(level):
    """Adjust screen brightness (Windows)"""
    try:
        # Try using WMI to adjust brightness
        import wmi
        c = wmi.WMI(namespace='wmi')
        methods = c.WmiMonitorBrightnessMethods()[0]
        methods.WmiSetBrightness(int(level), 0)
        return f"Brightness set to {level}%"
    except:
        # Alternative method using PowerShell (if available)
        try:
            import subprocess
            subprocess.run([
                'powershell', '-Command',
                f'(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})'
            ], check=True, capture_output=True)
            return f"Brightness set to {level}%"
        except:
            # Another alternative using registry or other methods
            try:
                # Try to use Windows API via ctypes
                import ctypes
                from ctypes import wintypes
                # This is a simplified approach - actual implementation would be more complex
                # For now, we'll return a message indicating the limitation
                pass
            except:
                pass
            return f"Unable to adjust brightness automatically. Manual adjustment needed for {level}%."

def get_running_processes():
    """Get list of running processes"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return processes

if __name__ == "__main__":
    print("Security Manager initialized")