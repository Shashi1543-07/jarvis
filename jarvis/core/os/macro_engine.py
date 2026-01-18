import pyautogui
import time
from core.os.window_manager import WindowManager

class MacroEngine:
    def __init__(self):
        self.wm = WindowManager()
        self.boss_key_active = False

    def activate_boss_key(self, cover_app="code"):
        """
        Instantly hides distractions and focuses a professional application.
        """
        print(f"MacroEngine: Activating Boss Key (Cover: {cover_app})")
        
        # 1. Minimize all
        pyautogui.hotkey('win', 'd')
        time.sleep(0.5)
        
        # 2. Open or focus cover app
        from actions.system_actions import open_application
        open_application(cover_app)
        
        time.sleep(1)
        self.wm.maximize(cover_app)
        self.wm.focus_window(cover_app)
        
        self.boss_key_active = True
        return f"Boss Key active. Work environment restored with {cover_app}."

    def execute_custom_macro(self, sequence):
        """
        Executes a sequence of keys.
        sequence: list of keys or hotkeys, e.g. [('ctrl', 'c'), 'down', ('ctrl', 'v')]
        """
        for s in sequence:
            if isinstance(s, tuple):
                pyautogui.hotkey(*s)
            else:
                pyautogui.press(s)
            time.sleep(0.1)
        return "Custom macro executed."
