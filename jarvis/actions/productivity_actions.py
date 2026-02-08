import time
import threading
import datetime
import os

def set_timer(seconds):
    print(f"Setting timer for {seconds} seconds")
    def timer_thread():
        time.sleep(seconds)
        print(f"TIMER DONE: {seconds} seconds have passed!")
        # In a real app, we'd play a sound or show a notification here
    
    t = threading.Thread(target=timer_thread)
    t.start()
    return f"Timer set for {seconds} seconds."

def set_alarm(time_str):
    # time_str format: "HH:MM" (24-hour)
    print(f"Setting alarm for {time_str}")
    def alarm_thread():
        while True:
            now = datetime.datetime.now().strftime("%H:%M")
            if now == time_str:
                print(f"ALARM! It is {time_str}!")
                break
            time.sleep(30)
    
    t = threading.Thread(target=alarm_thread)
    t.start()
    return f"Alarm set for {time_str}"

def create_reminder(text=None, task=None, time_str=None, **kwargs):
    """Simple reminder implementation - accepts both 'text' and 'task' for NLU compatibility"""
    reminder_text = text or task or kwargs.get("content", "")
    if not reminder_text:
        return "I didn't catch what you wanted me to remind you about."
    print(f"Reminder set: {reminder_text} at {time_str}")
    return f"Reminder set: {reminder_text}"


def todo_add(item):
    print(f"Adding to TODO: {item}")
    file_path = "todo.txt"
    with open(file_path, "a") as f:
        f.write(f"- {item}\n")
    return f"Added to TODO: {item}"

def todo_list():
    print("Listing TODO items...")
    file_path = "todo.txt"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            items = f.read()
        return items
    else:
        return "TODO list is empty."

def todo_delete(item):
    print(f"Deleting from TODO: {item}")
    file_path = "todo.txt"
    if not os.path.exists(file_path):
        return "TODO list is empty."
    
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    new_lines = [line for line in lines if item not in line]
    
    with open(file_path, "w") as f:
        f.writelines(new_lines)
    
    return f"Removed {item} from TODO list."

def summarize_document(file_path):
    """Analyze and summarize a local document"""
    from core.productivity.doc_analyzer import DocAnalyzer
    from core.ollama_brain import OllamaBrain
    da = DocAnalyzer(OllamaBrain())
    return da.summarize_document(file_path)

def ask_about_document(file_path, question):
    """Answer a specific question based on a document's content"""
    from core.productivity.doc_analyzer import DocAnalyzer
    from core.ollama_brain import OllamaBrain
    da = DocAnalyzer(OllamaBrain())
    return da.ask_about_document(file_path, question)

def explain_code(file_path, function_name=None):
    """Explain code logic or specific functions"""
    from core.productivity.code_assistant import CodeAssistant
    from core.ollama_brain import OllamaBrain
    ca = CodeAssistant(OllamaBrain())
    return ca.explain_code(file_path, function_name)

def analyze_project(root_path):
    """Analyze the architecture of a project directory"""
    from core.productivity.code_assistant import CodeAssistant
    from core.ollama_brain import OllamaBrain
    ca = CodeAssistant(OllamaBrain())
    return ca.analyze_project_structure(root_path)
