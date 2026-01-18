import psutil
import datetime
import os
from typing import Dict, Any

class BriefingManager:
    def __init__(self, memory, ollama_brain):
        self.memory = memory
        self.ollama = ollama_brain

    def generate_report(self) -> str:
        """Collects data and uses Ollama to generate a JARVIS-style briefing."""
        
        # 1. System Stats
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()
        batt_str = f"{battery.percent}% {'(Charging)' if battery.power_plugged else ''}" if battery else "N/A"
        
        # 2. Memory Context
        recent_convs = self.memory.get_short_term_as_string(count=5)
        recent_sessions = self.memory.get_recent_sessions(count=3)
        session_text = "\n".join([f"- {s['summary']}" for s in recent_sessions]) if recent_sessions else "No recent session summaries."
        
        # 3. Task info
        active_tasks = self.memory.list_tasks()
        tasks_text = ", ".join(active_tasks) if active_tasks else "None."

        # 4. Construct Prompt
        prompt = f"""
        Generate a JARVIS-style daily briefing based on the following data:
        
        CURRENT TIME: {datetime.datetime.now().strftime("%I:%M %p")}
        SYSTEM STATUS: CPU {cpu}%, RAM {ram}%, Battery {batt_str}
        
        RECENT INTERACTION THEMES:
        {recent_convs}
        
        RECENT SESSION SUMMARIES:
        {session_text}
        
        ACTIVE TASKS:
        {tasks_text}
        
        INSTRUCTIONS:
        Be extremely direct, factual, and concise. 
        Start with a status update, then summarize what has happened today, and end with any pending tasks.
        Use a professional and efficient tone.
        """
        
        system_msg = "You are JARVIS. Provide a direct and efficient status briefing."
        
        response = self.ollama.generate_response(prompt, system=system_msg)
        return response
