import pyautogui
import webbrowser

def play_music():
    print("Playing music...")
    # Simulating media key press
    pyautogui.press("playpause")

def pause_music():
    print("Pausing music...")
    pyautogui.press("playpause")

def next_track():
    print("Next track...")
    pyautogui.press("nexttrack")

def previous_track():
    print("Previous track...")
    pyautogui.press("prevtrack")

def set_volume(volume_level):
    # Re-implementing here or importing from system_actions if shared
    # For now, just a wrapper or we can remove it if system_actions handles it
    # The user list has set_volume under "media", so we should support it here too.
    from actions.system_actions import set_volume as sys_set_volume
    sys_set_volume(volume_level)

def mute_volume():
    from actions.system_actions import mute_volume as sys_mute_volume
    sys_mute_volume()

def unmute_volume():
    from actions.system_actions import unmute_volume as sys_unmute_volume
    sys_unmute_volume()
