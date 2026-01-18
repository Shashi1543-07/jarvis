import os
import pyautogui
import platform
import psutil
import datetime
import time


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
    try:
        # Try using pycaw for direct volume control
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Set volume scalar (0.0 to 1.0)
        scalar = float(volume_level) / 100.0
        volume.SetMasterVolumeLevelScalar(scalar, None)
        return f"Volume set to {volume_level}%"
    except ImportError:
        print("pycaw library not found. Falling back to key presses.")
    except Exception as e:
        print(f"pycaw error: {e}. Falling back to key presses.")

    # Fallback: Basic implementation using pyautogui
    # Reset to 0
    for _ in range(50):
        pyautogui.press("volumedown")
    # Increase to desired level (assuming each press is ~2%)
    presses = int(int(volume_level) / 2)
    pyautogui.press("volumeup", presses=presses)
    return f"Volume set to approximately {volume_level}%"

def mute_volume():
    print("Muting volume...")
    pyautogui.press("volumemute")
    return "Volume muted."

def unmute_volume():
    print("Unmuting volume...")
    pyautogui.press("volumemute")
    return "Volume unmuted."

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

def connect_wifi(ssid=None, password=None):
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

def disconnect_wifi():
    """Disconnect from WiFi"""
    import subprocess
    print("Disconnecting WiFi...")
    try:
        subprocess.run(["netsh", "wlan", "disconnect"], shell=True)
        return "WiFi disconnected."
    except Exception as e:
        return f"Failed to disconnect WiFi: {e}"

def toggle_bluetooth(state="on"):
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

def enable_hotspot():
    """Enable Mobile Hotspot"""
    # Requires admin and specific powershell scripts usually
    print("Enabling Hotspot...")
    try:
        subprocess.run(["start", "ms-settings:network-mobilehotspot"], shell=True)
        return "Opened Hotspot settings."
    except Exception as e:
        return f"Failed to enable hotspot: {e}"

def disable_hotspot():
    print("Disabling Hotspot...")
    try:
        subprocess.run(["start", "ms-settings:network-mobilehotspot"], shell=True)
        return "Opened Hotspot settings."
    except Exception as e:
        return f"Failed to disable hotspot: {e}"

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

def empty_recycle_bin():
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
    """Put system to sleep"""
    print("Putting system to sleep...")
    if platform.system() == "Windows":
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif platform.system() == "Darwin":
        os.system("pmset sleepnow")
    elif platform.system() == "Linux":
        os.system("systemctl suspend")
    return "System is going to sleep."

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

def close_application(app_name):
    """Close a specific application by name"""
    try:
        if platform.system() == "Windows":
            os.system(f"taskkill /im {app_name}.exe /f")
            return f"Closed {app_name}."
        else:
            return f"Closing applications is currently only supported on Windows."
    except Exception as e:
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

def activate_boss_key(cover_app="code"):
    """Instantly hide distractions and focus a work app"""
    from core.os.macro_engine import MacroEngine
    me = MacroEngine()
    return me.activate_boss_key(cover_app)
