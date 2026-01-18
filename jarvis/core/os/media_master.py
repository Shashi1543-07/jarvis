import pyautogui
import time

class MediaMaster:
    def __init__(self):
        print("MediaMaster: Initialized.")

    def play_pause(self):
        """Toggles play/pause state globally."""
        pyautogui.press("playpause")
        return "Toggled playback."

    def stop(self):
        """Stops playback."""
        pyautogui.press("stop")
        return "Stopped playback."

    def next_track(self):
        """Skips to the next track."""
        pyautogui.press("nexttrack")
        return "Skipped to next track."

    def prev_track(self):
        """Returns to the previous track."""
        pyautogui.press("prevtrack")
        return "Went back to previous track."

    def volume_up(self, steps=5):
        """Increases system volume."""
        for _ in range(steps):
            pyautogui.press("volumeup")
        return f"Volume increased by {steps} steps."

    def volume_down(self, steps=5):
        """Decreases system volume."""
        for _ in range(steps):
            pyautogui.press("volumedown")
        return f"Volume decreased by {steps} steps."

    def mute(self):
        """Mutes/Unmutes volume."""
        pyautogui.press("volumemute")
        return "Muted/Unmuted volume."
