import pygetwindow as gw
import time
import win32gui
import win32con

class WindowManager:
    def __init__(self):
        print("WindowManager: Initialized.")

    def list_windows(self):
        """Returns a list of titles of all visible windows."""
        return [win.title for win in gw.getAllWindows() if win.title.strip()]

    def find_window(self, name):
        """Finds a window containing the given name."""
        all_windows = gw.getWindowsWithTitle(name)
        if all_windows:
            return all_windows[0]
        return None

    def focus_window(self, name):
        """Brings a window to the front."""
        win = self.find_window(name)
        if win:
            if win.isMinimized:
                win.restore()
            win.activate()
            return True
        return False

    def tile_windows(self, win1_name, win2_name):
        """Tiles two windows side-by-side (Vertical split)."""
        win1 = self.find_window(win1_name)
        win2 = self.find_window(win2_name)

        if not win1 or not win2:
            return False, f"Could not find one or both windows: {win1_name}, {win2_name}"

        # Get screen metrics (Simple approach for single monitor)
        # We'll use pygetwindow's screen properties if available, or assume standard.
        # But easier to just move them to left/right halves.
        
        # Restore if minimized
        if win1.isMinimized: win1.restore()
        if win2.isMinimized: win2.restore()

        # Rough screen width detection via an maximized window or just 1920
        screen_w = 1920 # Default fallback
        screen_h = 1080
        
        # Try to get active screen size
        try:
            # Note: pygetwindow doesn't easily give monitor size.
            # Using win32gui as fallback
            from win32api import GetSystemMetrics
            screen_w = GetSystemMetrics(0)
            screen_h = GetSystemMetrics(1)
        except:
            pass

        # Position Win1 (Left Half)
        win1.moveTo(0, 0)
        win1.resizeTo(screen_w // 2, screen_h - 40) # Subtract taskbar height

        # Position Win2 (Right Half)
        win2.moveTo(screen_w // 2, 0)
        win2.resizeTo(screen_w // 2, screen_h - 40)

        win1.activate()
        return True, f"Tiled {win1_name} and {win2_name}."

    def maximize(self, name):
        win = self.find_window(name)
        if win:
            win.maximize()
            return True
        return False

    def minimize_all_except(self, keep_name):
        """Minimizes all windows except the one specified."""
        keep_win = self.find_window(keep_name)
        for win in gw.getAllWindows():
            if win.title.strip() and win != keep_win and not win.isMinimized:
                # Avoid minimizing the taskbar or desktop
                if "Program Manager" not in win.title and "Settings" not in win.title:
                    win.minimize()
        return True
