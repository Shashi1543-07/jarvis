def go_to_sleep():
    """
    Put Jarvis into sleep mode.
    In this mode, Jarvis will only listen for 'Wake up' or 'Hey Jarvis'.
    """
    return "Entering sleep mode."

def enable_sleep_mode():
    """Alias for go_to_sleep to handle legacy LLM predictions"""
    return go_to_sleep()

def wake_up():
    """
    Wake Jarvis from sleep mode.
    """
    return "Waking up."

def stop_speaking():
    """
    Stop the current speech output.
    """
    return "Speech stopped."

def voice_listen_start():
    return "Listening started."

def voice_listen_stop():
    return "Listening stopped."

def change_state(state):
    return f"State changed to {state}"

def restart_ai_brain():
    return "AI Brain restarting..."

def debug_log(message):
    print(f"DEBUG LOG: {message}")
    return "Logged."
