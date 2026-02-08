import os
import pyautogui
import platform
import psutil
import datetime
import time
import pygetwindow as gw


def shutdown_system():
    print("Shutting down system...")
    if platform.system() == "Windows":
        os.system("shutdown /s /t 5")
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        os.system("shutdown now")

def lock_system():
    print("Locking system...")
    if platform.system() == "Windows":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif platform.system() == "Darwin":
        os.system("pmset displaysleepnow")
    elif platform.system() == "Linux":
        os.system("gnome-screensaver-command -l") 

def put_computer_to_sleep():
    """Put the computer hardware into sleep/suspend mode"""
    print("Putting system to sleep...")
    if platform.system() == "Windows":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif platform.system() == "Darwin":
        os.system("pmset sleepnow")
    elif platform.system() == "Linux":
        os.system("systemctl suspend")
    return "System is going to sleep."

def set_volume(volume_level):
    """
    Set system volume to a specific percentage (0-100).
    """
    print(f"Setting volume to {volume_level}%")
    success = False
    
    # 1. Try pycaw with robust device iteration
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        # Get all devices rather than relying on GetSpeakers() which can be buggy
        devices = AudioUtilities.GetAllDevices()
        
        scalar = float(volume_level) / 100.0
        
        for device in devices:
            # Try to activate the interface on each device
            # We target Active devices usually, or all to be safe
            try:
                # Based on debug output, these might handle activation internally 
                # or we accept the raw interface if available. But typical pycaw usage:
                interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterVolumeLevelScalar(scalar, None)
                success = True
            except Exception as d_e:
                # Some devices (mics) might fail or lack the interface
                pass
                
        if success:
            return f"Volume set to {volume_level}%"
    except Exception as e:
        print(f"Direct volume error: {e}")

    # 2. Optimized Fallback (Fast Reset)
    # If pycaw managed to do nothing or failed, we use keyboard.
    print("Using fast fallback for volume...")
    
    # Temporarily speed up pyautogui
    original_pause = pyautogui.PAUSE
    pyautogui.PAUSE = 0.01 
    
    try:
        # 1. Mute to ensure we are silent (optional, but resetting to 0 is safer for absolute)
        # Actually resetting to 0 via 50 down presses is reliable
        pyautogui.press("volumedown", presses=50)
        
        # 2. Go up to target. 50 presses = 100% usually (step is often 2%)
        steps = int(int(volume_level) / 2)
        pyautogui.press("volumeup", presses=steps)
    finally:
        pyautogui.PAUSE = original_pause
        
    return f"Volume set to approx {volume_level}% (via Fallback)"

def mute_volume():
    print("Muting volume...")
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1, None)
        return "System muted."
    except:
        pyautogui.press("volumemute")
        return "Volume muted toggle triggered."

def unmute_volume():
    print("Unmuting volume...")
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(0, None)
        return "System unmuted."
    except:
        pyautogui.press("volumemute")
        return "Volume unmute toggle triggered."

def increase_volume(step=10):
    """Increase system volume by a step value"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        current = volume.GetMasterVolumeLevelScalar()
        new_volume = min(1.0, current + (float(step) / 100.0))
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        return f"Volume increased to {round(new_volume * 100)}%"
    except Exception as e:
        # Fallback
        pyautogui.press("volumeup", presses=int(step/2))
        return f"Volume increased by approximately {step}%"

def decrease_volume(step=10):
    """Decrease system volume by a step value"""
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        current = volume.GetMasterVolumeLevelScalar()
        new_volume = max(0.0, current - (float(step) / 100.0))
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        return f"Volume decreased to {round(new_volume * 100)}%"
    except Exception as e:
        # Fallback
        pyautogui.press("volumedown", presses=int(step/2))
        return f"Volume decreased by approximately {step}%"

def set_brightness(level):
    """
    Set screen brightness to a specific percentage (0-100).
    Uses lazy loading to ensure the module is available at runtime.
    """
    try:
        # Lazy import - attempt to import fresh each time to avoid cached import failures
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
        print(f"Brightness set to {level}%")
        return f"Brightness set to {level}%"
    except ImportError as e:
        error_msg = "screen_brightness_control module not installed or dependencies missing."
        print(error_msg)
        print(f"Import error details: {e}")
        return f"Brightness control unavailable. Please reinstall: pip install screen-brightness-control"
    except Exception as e:
        print(f"Error setting brightness: {e}")
        return f"Failed to set brightness: {e}"

def take_screenshot():
    print("Taking screenshot...")
    # Use OneDrive Screenshots folder
    screenshots_dir = r"C:\Users\lenovo\OneDrive\Pictures\Screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = os.path.join(screenshots_dir, filename)
    
    try:
        img = pyautogui.screenshot()
        img.save(filepath)
        abs_path = os.path.abspath(filepath)
        print(f"Screenshot saved to {abs_path}")
        return f"Screenshot saved successfully to {abs_path}"
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return f"Failed to take screenshot: {e}"

def record_screen(duration=10):
    # Basic implementation using OpenCV/numpy/pyautogui could go here
    # For now, just a placeholder as it requires more dependencies
    print(f"Recording screen for {duration} seconds... (Not implemented)")
    return "Screen recording not yet implemented."

def check_time():
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"Current time: {now}")
    return f"The current time is {now}"

def check_date():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"Current date: {today}")
    return f"Today's date is {today}"

def system_status():
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    status = f"CPU Usage: {cpu}%\nMemory Usage: {memory}%\nDisk Usage: {disk}%"
    print(status)
    return status

def cpu_usage():
    usage = psutil.cpu_percent()
    return f"CPU Usage is at {usage}%"

def ram_usage():
    usage = psutil.virtual_memory().percent
    return f"RAM Usage is at {usage}%"

def battery_status():
    battery = psutil.sensors_battery()
    if battery:
        plugged = "plugged in" if battery.power_plugged else "not plugged in"
        return f"Battery is at {battery.percent}% and is {plugged}."
    else:
        return "Battery status not available (desktop?)."

def system_performance():
    """
    Get a summary of system performance (CPU, Memory, Disk).
    """
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    status = (
        f"System Performance:\n"
        f"- CPU Usage: {cpu}%\n"
        f"- Memory Usage: {memory}%\n"
        f"- Disk Usage: {disk}%"
    )
    print(status)
    return status

# --- New Connectivity Actions ---

def connect_wifi(ssid=None, password=None, **kwargs):
    """Connect to a WiFi network"""
    import subprocess
    print(f"Connecting to WiFi: {ssid}")
    try:
        # If no SSID provided, just enable WiFi
        if not ssid:
            subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "admin=enabled"], shell=True)
            return "WiFi enabled."
            
        # Connect to specific network (requires profile to exist usually, or complex xml)
        # For now, let's try basic connection if profile exists
        cmd = f'netsh wlan connect name="{ssid}"'
        subprocess.run(cmd, shell=True)
        return f"Attempting to connect to {ssid}..."
    except Exception as e:
        return f"Failed to connect to WiFi: {e}"

def disconnect_wifi(**kwargs):
    """Disconnect from WiFi"""
    import subprocess
    print("Disconnecting WiFi...")
    try:
        subprocess.run(["netsh", "wlan", "disconnect"], shell=True)
        return "WiFi disconnected."
    except Exception as e:
        return f"Failed to disconnect WiFi: {e}"

def toggle_bluetooth(state="on", **kwargs):
    """Toggle Bluetooth (Windows 10/11 is tricky via cmd, using powershell or placeholder)"""
    # Note: Windows doesn't have a simple native CLI for bluetooth toggle without 3rd party tools
    # We can try PowerShell UWP calls but it's complex. 
    # For now, we'll open settings as a fallback or use a known registry hack if possible.
    # A reliable way is opening the settings page.
    import subprocess
    print(f"Toggling Bluetooth {state}...")
    try:
        subprocess.run(["start", "ms-settings:bluetooth"], shell=True)
        return f"Opened Bluetooth settings to turn {state}."
    except Exception as e:
        return f"Failed to toggle Bluetooth: {e}"

def enable_hotspot(**kwargs):
    """Enable Mobile Hotspot"""
    import subprocess
    # Requires admin and specific powershell scripts usually
    print("Enabling Hotspot...")
    try:
        subprocess.run(["start", "ms-settings:network-mobilehotspot"], shell=True)
        return "Opened Hotspot settings."
    except Exception as e:
        return f"Failed to enable hotspot: {e}"

def disable_hotspot(**kwargs):
    print("Disabling Hotspot...")
    try:
        import subprocess
        subprocess.run(["start", "ms-settings:network-mobilehotspot"], shell=True)
        return "Opened Hotspot settings."
    except Exception as e:
        return f"Failed to disable hotspot: {e}"

def handle_hotspot(state="on", **kwargs):
    """Dispatcher for Hotspot state"""
    if "off" in state.lower() or "disable" in state.lower():
        return disable_hotspot()
    return enable_hotspot()

def restart_pc():
    print("Restarting PC...")
    if platform.system() == "Windows":
        os.system("shutdown /r /t 5")
    return "Restarting system in 5 seconds."

def log_out():
    print("Logging out...")
    if platform.system() == "Windows":
        os.system("shutdown /l")
    return "Logging out..."

def empty_recycle_bin(**kwargs):
    import winshell
    try:
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        return "Recycle bin emptied."
    except Exception as e:
        return f"Failed to empty recycle bin: {e}"

def open_task_manager():
    pyautogui.hotkey('ctrl', 'shift', 'esc')
    return "Opened Task Manager."

def increase_brightness(step=10):
    """Increase screen brightness by a step value"""
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness()[0]  # Get current brightness
        new_brightness = min(100, current + step)  # Ensure it doesn't exceed 100%
        sbc.set_brightness(new_brightness)
        return f"Brightness increased to {new_brightness}%"
    except ImportError:
        return "Brightness control not available. Install screen-brightness-control."
    except Exception as e:
        return f"Failed to adjust brightness: {e}"

def decrease_brightness(step=10):
    """Decrease screen brightness by a step value"""
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness()[0]  # Get current brightness
        new_brightness = max(0, current - step)  # Ensure it doesn't go below 0%
        sbc.set_brightness(new_brightness)
        return f"Brightness decreased to {new_brightness}%"
    except ImportError:
        return "Brightness control not available. Install screen-brightness-control."
    except Exception as e:
        return f"Failed to adjust brightness: {e}"

def adjust_brightness():
    """Interactive brightness adjustment"""
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness()[0]
        return f"Current brightness is {current}%. You can specify a percentage to set it to."
    except ImportError:
        return "Brightness control not available. Install screen-brightness-control."
    except Exception as e:
        return f"Failed to get brightness: {e}"

def sleep_system():
    """Put system to sleep (Configured to Lock Screen)"""
    print("Locking system (User preference for sleep)...")
    if platform.system() == "Windows":
        # User requested "sleep" command to just lock the screen
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif platform.system() == "Darwin":
        os.system("pmset displaysleepnow")
    elif platform.system() == "Linux":
        # Locking screen usually depends on the desktop environment (gnome, kde, etc)
        # Using a common one or falling back to sleep if lock not found is tricky, 
        # but for now we'll stick to the requested behavior adjustment for Windows primarily.
        os.system("gnome-screensaver-command -l") 
    return "Screen locked (System Sleep mode)."

def restart_system():
    """Restart the system"""
    print("Restarting system...")
    if platform.system() == "Windows":
        os.system("shutdown /r /t 5")
    elif platform.system() == "Linux" or platform.system() == "Darwin":
        os.system("sudo reboot")
    return "System restarting in 5 seconds."

def hibernate_system():
    """Hibernate the system"""
    print("Hibernating system...")
    if platform.system() == "Windows":
        os.system("shutdown /h")
    elif platform.system() == "Linux":
        os.system("systemctl hibernate")
    # Darwin (macOS) doesn't have a simple hibernation command
    return "System hibernating."

def check_day():
    """Get the current day of the week"""
    day = datetime.datetime.now().strftime("%A")
    return f"Today is {day}"

def memory_usage():
    """Get memory usage"""
    usage = psutil.virtual_memory().percent
    return f"Memory usage is at {usage}%"

def disk_usage():
    """Get disk usage"""
    usage = psutil.disk_usage('/').percent
    return f"Disk usage is at {usage}%"

def network_status():
    """Get network status"""
    try:
        import socket
        # Try to connect to a public DNS server to check internet connectivity
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return "Network is connected to the internet."
    except OSError:
        return "Network is not connected to the internet."

def open_application(app_name):
    """Open a specific application by name"""
    try:
        if platform.system() == "Windows":
            # Common Windows applications
            apps = {
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "paint": "mspaint.exe",
                "wordpad": "write.exe",
                "cmd": "cmd.exe",
                "powershell": "powershell.exe",
                "explorer": "explorer.exe",
                "chrome": "chrome.exe",
                "firefox": "firefox.exe",
                "edge": "msedge.exe",
                "vscode": "code.exe",
                "spotify": "spotify.exe",
                "steam": "steam.exe",
                "discord": "discord.exe"
            }

            app_cmd = apps.get(app_name.lower(), app_name)
            os.system(f"start {app_cmd}")
            return f"Opening {app_name}."
        else:
            # For Linux/Mac, we'd need different handling
            return f"Opening applications is currently only supported on Windows."
    except Exception as e:
        return f"Failed to open {app_name}: {e}"

def close_application(app_name, **kwargs):
    """Close a specific application by name"""
    try:
        if platform.system() == "Windows":
            # Map common names to process names
            apps = {
                "notepad": "notepad.exe",
                "calculator": "calc.exe",
                "paint": "mspaint.exe",
                "wordpad": "write.exe",
                "cmd": "cmd.exe",
                "powershell": "powershell.exe",
                "explorer": "explorer.exe",
                "chrome": "chrome.exe",
                "google chrome": "chrome.exe",
                "firefox": "firefox.exe",
                "edge": "msedge.exe",
                "microsoft edge": "msedge.exe",
                "brave": "brave.exe",
                "brave browser": "brave.exe",
                "opera": "opera.exe",
                "vivaldi": "vivaldi.exe",
                "vscode": "code.exe",
                "vs code": "code.exe",
                "visual studio code": "code.exe",
                "code": "code.exe",
                "spotify": "spotify.exe",
                "steam": "steam.exe",
                "discord": "discord.exe",
                "telegram": "telegram.exe",
                "whatsapp": "whatsapp.exe",
                "slack": "slack.exe",
                "teams": "teams.exe",
                "microsoft teams": "teams.exe",
                "zoom": "zoom.exe",
                "vlc": "vlc.exe",
                "word": "winword.exe",
                "excel": "excel.exe",
                "powerpoint": "powerpnt.exe",
                "outlook": "outlook.exe",
            }

            
            # Clean app name (remove trailing punctuation)
            clean_name = app_name.lower().strip().rstrip('.')
            
            process_name = apps.get(clean_name, f"{clean_name}.exe")
            
            # Handle case where .exe was already in the mapping or provided
            if not process_name.endswith(".exe"):
                 process_name += ".exe"
                 
            # Check if still open, if so, fall through to taskkill
            if not gw.getWindowsWithTitle(clean_name):
                os.system(f"taskkill /im {process_name} /f")
                return f"Closed {clean_name} ({process_name})."
            else:
                # If windows are found, try to close them gracefully first
                windows = gw.getWindowsWithTitle(clean_name)
                for window in windows:
                    try:
                        window.close()
                    except Exception as win_e:
                        print(f"Error closing window {window.title}: {win_e}")
                # If after trying to close windows, they are still there, force kill
                if gw.getWindowsWithTitle(clean_name):
                    os.system(f"taskkill /im {process_name} /f")
                    return f"Attempted graceful close, then force closed {clean_name} ({process_name})."
                return f"Closed {clean_name} windows."
        else:
            return f"Closing applications is currently only supported on Windows."
    except Exception as e:
        print(f"Window close error: {e}")
        return f"Failed to close {app_name}: {e}"

def system_info():
    """Get comprehensive system information"""
    import platform
    uname = platform.uname()
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())

    info = f"""
System Information:
- System: {uname.system}
- Node Name: {uname.node}
- Release: {uname.release}
- Version: {uname.version}
- Machine: {uname.machine}
- Processor: {uname.processor}
- Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
    """
    return info.strip()

def list_processes():
    """List running processes"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Process might have terminated or access denied

    # Return first 10 processes for brevity
    top_processes = processes[:10]
    process_list = "\n".join([f"- {p['name']} (PID: {p['pid']})" for p in top_processes])
    return f"Top running processes:\n{process_list}\n... and {len(processes)-10} more."

def kill_process_by_name(process_name):
    """Kill a process by its name"""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if process_name.lower() in proc.info['name'].lower():
                proc.kill()
                return f"Killed process {proc.info['name']} (PID: {proc.info['pid']})"
        return f"No process found with name containing '{process_name}'"
    except Exception as e:
        return f"Failed to kill process: {e}"

# --- Window Management Actions ---

def list_open_windows():
    """List all open window titles"""
    from core.os.window_manager import WindowManager
    wm = WindowManager()
    windows = wm.list_windows()
    if windows:
        return f"Currently open windows:\n" + "\n".join([f"- {w}" for w in windows])
    return "No visible windows found."

def focus_app(name):
    """Bring a specific application to the front"""
    from core.os.window_manager import WindowManager
    wm = WindowManager()
    if wm.focus_window(name):
        return f"Focused {name}."
    return f"Could not find a window with name {name}."

def tile_apps(app1, app2):
    """Tile two applications side-by-side"""
    from core.os.window_manager import WindowManager
    wm = WindowManager()
    success, msg = wm.tile_windows(app1, app2)
    return msg

def maximize_app(name):
    """Maximize a specific application"""
    from core.os.window_manager import WindowManager
    wm = WindowManager()
    if wm.maximize(name):
        return f"Maximized {name}."
    return f"Window {name} not found."

    me = MacroEngine()
    return me.activate_boss_key(cover_app)

def handle_system_control(**kwargs):
    """
    Dispatcher for SYSTEM_CONTROL intent.
    Accepts loose kwargs to avoid crashes and routes to specific functions.
    """
    print(f"System Control Dispatch: {kwargs}")
    
    # 1. Check for specific command/action slots
    command = kwargs.get("command") or kwargs.get("action") or kwargs.get("operation")
    
    # 2. Heuristics based on other slots if command is missing
    # (Sometimes NLU puts 'restart' in 'app_name' if confused)
    if not command:
        for val in kwargs.values():
            if isinstance(val, str):
                if "restart" in val.lower(): command = "restart"
                elif "shutdown" in val.lower(): command = "shutdown"
                elif "sleep" in val.lower(): command = "sleep"
    
    if command:
        cmd = command.lower()
        if "restarts" in cmd or "restart" in cmd: return restart_system()
        if "shutdown" in cmd: return shutdown_system()
        if "sleep" in cmd: return sleep_system()
        if "lock" in cmd: return lock_system()
        if "logout" in cmd or "log out" in cmd: return log_out()
        if "hibernate" in cmd: return hibernate_system()
        if "unmute" in cmd: return unmute_volume()
        elif "mute" in cmd: return mute_volume()
        if "screenshot" in cmd: return take_screenshot()
        
        # Added missing handlers based on log analysis
        if "volume" in cmd:
            import re
            all_text = f"{cmd} {kwargs.get('content', '')} {kwargs.get('text', '')}".lower()
            nums = re.findall(r'(\d+)', all_text)
            if nums:
                val = int(nums[0])
                if "to" in all_text or "set" in all_text or "at" in all_text:
                    return set_volume(val)
                elif "increase" in all_text or "up" in all_text:
                    return increase_volume(val)
                elif "decrease" in all_text or "down" in all_text:
                    return decrease_volume(val)
                return set_volume(val)
            elif "increase" in cmd or "up" in cmd:
                return increase_volume()
            elif "decrease" in cmd or "down" in cmd or "decrease_volume" in cmd or "volume_decrease" in cmd:
                return decrease_volume()
            return set_volume(50)

        if "brightness" in cmd:
            import re
            all_text = f"{cmd} {kwargs.get('content', '')} {kwargs.get('text', '')}".lower()
            nums = re.findall(r'(\d+)', all_text)
            
            if nums:
               val = int(nums[0])
               # "increase to 100%" or "set to 80%" or just "80%" -> absolute
               if "to" in all_text or "set" in all_text or "at" in all_text:
                   return set_brightness(val)
               # "increase by 20%" or "up 20%" -> relative
               elif "increase" in all_text or "up" in all_text:
                   return increase_brightness(val)
               elif "decrease" in all_text or "down" in all_text:
                   return decrease_brightness(val)
               # Default for "brightness 50" -> absolute
               return set_brightness(val)
            elif "increase" in cmd:
               return increase_brightness()
            elif "decrease" in cmd:
               return decrease_brightness()
            return adjust_brightness()
        
        if "battery" in cmd: return battery_status()
        if "performance" in cmd or "status" in cmd: return system_performance()
         
    # 3. Fallback to System Info (safe default) if no specific command identified
    # But do NOT crash if args are present
    return system_info()
