import json
import os
import random
from datetime import datetime
from core.ollama_brain import OllamaBrain
from core.internet.research_agent import ResearchAgent
import re

class LocalBrain:
    """A highly functional Local Brain that maps intents to actions and varied responses."""

    def __init__(self, memory):
        self.memory = memory
        self.ollama = OllamaBrain() # Local LLM interface
        self.research_agent = ResearchAgent(self.ollama)
        self.visual_cache = {} # Stores last seen objects/scene

        # Jarvis-style conversational templates (Fast response)
        self.templates = {
            "GREETING": ["Hello Sir, standing by.", "At your service, Sir.", "Welcome back. How can I assist today?", "Systems online and ready.", "Ready for your command, Sir."],
            "THANKS": ["My pleasure, Sir.", "Always happy to help.", "Of course.", "Anytime.", "Just doing my job, Sir."],
            "WHO_CREATED": ["I was designed by you, Sir, to be the ultimate assistant.", "I am a product of your engineering, Sir.", "You are my creator.", "Created by you, for you, Sir."],
            "OFFLINE_FALLBACK": ["I'm currently operating in offline mode for efficiency.", "My web brain is idle, so I'm handling this locally.", "Processing locally to preserve bandwidth, Sir.", "Server connection unavailable, sir. Utilizing local protocols."],
            "NOT_UNDERSTOOD": ["I'm afraid I didn't quite catch that, Sir.", "Could you repeat that? Local processing is a bit narrow today.", "I'm having trouble analyzing that locally. Perhaps rephrase?"],
            "SYSTEM_STATUS": [
                "All systems nominal, Sir.",
                "All systems green, Sir.",
                "Operational parameters optimal.",
                "Running at peak efficiency, Sir."
            ]
        }

    def process(self, text, classification):
        text = text.lower().strip()

        # 1. Handle ACTION_REQUEST (Expanded capabilities)
        if classification == "ACTION_REQUEST":
            # Vision and camera controls
            if "eyes" in text or "camera" in text:
                return {"action": "open_camera", "text": "Eyes open, Sir."}

            # Web and application controls
            if "youtube" in text:
                return {"action": "open_website", "params": {"url": "https://www.youtube.com"}, "text": "Opening YouTube for you."}
            if "google" in text and "open" in text:
                return {"action": "open_website", "params": {"url": "https://www.google.com"}, "text": "Opening Google."}
            if "chrome" in text:
                return {"action": "open_app", "params": {"app_name": "chrome"}, "text": "Launching Chrome."}
            if "notepad" in text:
                return {"action": "open_app", "params": {"app_name": "notepad"}, "text": "Opening Notepad."}
            if "calculator" in text or "calc" in text:
                return {"action": "open_app", "params": {"app_name": "calc"}, "text": "Opening Calculator."}

            # Vision Action Handling (Enhanced)
            if "read" in text or "text" in text:
                return {"action": "read_text", "text": "Scanning for text..."}
            if "holding" in text or "hand" in text:
                return {"action": "detect_handheld_object", "text": "Analyzing what you are holding..."}
            if "who" in text and ("see" in text or "front" in text or "is that" in text):
                return {"action": "identify_people", "text": "Identifying people..."}
            if "recognise" in text or "recognize" in text or "identify" in text:
                return {"action": "identify_people", "text": "Scanning faces..."}
            if "describe" in text or "what do you see" in text or "analyse" in text or "analyze" in text:
                return {"action": "describe_scene", "text": "Analyzing the scene..."}
            if "objects" in text or "detect" in text or "scan" in text or "see" in text or "check" in text:
                # Group all general detection into detect_objects for Brain to summarize
                return {"action": "detect_objects", "text": "Scanning the environment, Sir."}

            # More specific actions
            if "screenshot" in text:
                return {"action": "take_screenshot", "text": "Capturing screenshot."}
            if "lock" in text:
                return {"action": "lock_system", "text": "Locking system."}
            if "brightness" in text:
                if "up" in text or "+" in text:
                    return {"action": "increase_brightness", "text": "Increasing brightness."}
                elif "down" in text or "-" in text:
                    return {"action": "decrease_brightness", "text": "Decreasing brightness."}
                else:
                    return {"action": "adjust_brightness", "text": "Adjusting brightness."}

        # 2. Handle SYSTEM_COMMAND (Enhanced)
        if classification == "SYSTEM_COMMAND":
            if "time" in text:
                now = datetime.now().strftime("%I:%M %p")
                return {"action": "check_time", "text": f"The time is {now}."}
            if "date" in text:
                today = datetime.now().strftime("%A, %B %d, %Y")
                return {"action": "check_date", "text": f"Today's date is {today}."}
            if "day" in text:
                day = datetime.now().strftime("%A")
                return {"action": "check_day", "text": f"Today is {day}."}
            if "volume" in text:
                if "up" in text or "+" in text:
                    return {"action": "set_volume", "params": {"volume_level": 80}, "text": "Volume increased."}
                elif "down" in text or "-" in text:
                    return {"action": "set_volume", "params": {"volume_level": 20}, "text": "Volume decreased."}
                elif "mute" in text:
                    return {"action": "mute_volume", "text": "Volume muted."}
                elif "up" in text or "+" in text:
                    return {"action": "volume_up", "text": "Turning it up."}
                elif "down" in text or "-" in text:
                    return {"action": "volume_down", "text": "Turning it down."}
                else:
                    return {"action": "set_volume", "params": {"volume_level": 50}, "text": "Setting volume to medium."}
            
            # Media Controls
            if any(x in text for x in ["music", "song", "track", "playback", "pause", "resume", "next", "previous"]):
                if "next" in text:
                    return {"action": "next_track", "text": "Skipping to next track."}
                if "previous" in text or "back" in text:
                    return {"action": "previous_track", "text": "Going back one track."}
                if "pause" in text:
                    return {"action": "pause_music", "text": "Music paused."}
                if "resume" in text or "play" in text:
                    return {"action": "play_music", "text": "Resuming playback."}
                if "stop" in text:
                    return {"action": "stop_music", "text": "Stopping playback."}
            if "battery" in text:
                return {"action": "battery_status", "text": "Checking power reserves."}
            if "briefing" in text or "report" in text or "what did i do" in text or "summary" in text:
                return {"action": "generate_daily_briefing", "text": "Gathering your daily briefing, Sir."}
            if "cpu" in text or "processor" in text:
                return {"action": "cpu_usage", "text": "Monitoring processor usage."}
            if "memory" in text or "ram" in text:
                return {"action": "memory_usage", "text": "Checking memory usage."}
            if "shutdown" in text or "power off" in text:
                return {"action": "shutdown_system", "text": "Shutting down system."}
            if "restart" in text:
                return {"action": "restart_system", "text": "Restarting system."}
            if "sleep" in text or "hibernate" in text:
                return {"action": "sleep_system", "text": "Putting system to sleep."}

            if "window" in text or "screen" in text or "tile" in text or "split" in text or "focus" in text or "maximize" in text:
                if "list" in text:
                    return {"action": "list_open_windows", "text": "Checking for open windows, Sir."}
                if "split" in text or "tile" in text:
                    # Try to extract app names: "split screen between X and Y"
                    import re
                    match = re.search(r"(?:split|tile)\s+(?:screen\s+)?(?:between\s+)?(\w+)\s+(?:and\s+)?(\w+)", text)
                    if match:
                        app1, app2 = match.groups()
                    return {"action": "tile_apps", "params": {"app1": app1, "app2": app2}, "text": f"Tiling {app1} and {app2} side-by-side."}
                    return {"text": "Sir, please specify which two applications I should tile."}
                
                if "summarize" in text or "analyze" in text or "analyse" in text:
                    # Extract file path: "summarize c:/path/to/file.pdf"
                    parts = text.split(" ")
                    file_path = next((p for p in parts if "." in p and os.path.exists(p)), None)
                    if file_path:
                        return {"action": "summarize_document", "params": {"file_path": file_path}, "text": f"Analyzing {os.path.basename(file_path)}, Sir. I will provide a summary shortly."}
                    return {"text": "Sir, please provide the path to the document you wish me to analyze."}

                if "focus" in text:
                    app = text.split("focus")[-1].strip()
                    if app: return {"action": "focus_app", "params": {"name": app}, "text": f"Switching focus to {app}."}
                
                if "organize" in text and ("folder" in text or "directory" in text):
                    # Extract path: "organize folder c:/users/..."
                    parts = text.split(" ")
                    folder_path = next((p for p in parts if os.path.isdir(p)), ".")
                    return {"action": "organize_folder", "params": {"path": folder_path}, "text": f"Organizing folders in {folder_path}, Sir."}

                if "explain" in text and ("code" in text or "function" in text):
                    # Extract file path: "explain code c:/path/to/file.py"
                    parts = text.split(" ")
                    file_path = next((p for p in parts if "." in p and os.path.exists(p)), None)
                    func_name = None
                    if "function" in text:
                        func_name = text.split("function")[-1].strip().split(" ")[0]
                    if file_path:
                        return {"action": "explain_code", "params": {"file_path": file_path, "function_name": func_name}, "text": f"Analyzing the code in {os.path.basename(file_path)}, Sir."}
                
                if "analyze" in text and "project" in text:
                    # Extract path: "analyze project c:/path/to/root"
                    parts = text.split(" ")
                    root_path = next((p for p in parts if os.path.isdir(p)), ".")
                    return {"action": "analyze_project", "params": {"root_path": root_path}, "text": f"Mapping the project architecture in {root_path}, Sir."}
                if "maximize" in text:
                    app = text.split("maximize")[-1].strip()
                    if app: return {"action": "maximize_app", "params": {"name": app}, "text": f"Maximizing {app}."}
                if any(x in text for x in ["boss", "hide everything", "clear screen", "privacy"]):
                    return {"action": "activate_boss_key", "params": {"cover_app": "code"}, "text": "Activating Boss Key, Sir. Desktop secured."}

        # 3. Handle PERSONAL_QUERY (Enhanced)
        if classification == "PERSONAL_QUERY":
            if "name" in text:
                name = self.memory.get("user_name") or "Sir"
                return {"text": f"Your name is {name}."}
            if "who created" in text or "developer" in text:
                return {"text": random.choice(self.templates["WHO_CREATED"])}
            if "who am i" in text or "who i am" in text or "my identity" in text:
                return {"text": "You are the user I was built to serve. My Commander."}
            if "who are you" in text or "your name" in text:
                 return {"text": "I am Jarvis. Your personal AI assistant."}
            # 1. Memorization Commands (Saving info)
            if any(term in text for term in ["memorize that", "memorise that", "remember that", "save that", "save this"]):
                trigger = next((t for t in ["memorize that", "memorise that", "remember that", "save that", "save this"] if t in text), None)
                to_remember = text.split(trigger)[-1].strip()
                if to_remember:
                    return {"action": "memorize_fact", "params": {"fact": to_remember}, "text": f"Understood, Sir. I've committed that to memory: {to_remember}."}
                return {"text": "What precisely would you like me to memorize, Sir?"}

            # 2. Recall Queries (Retrieving info)
            if any(term in text for term in ["recall", "remind", "what is", "what was", "do you remember", "tell me about"]):
                trigger = next((t for t in ["recall", "remind me about", "remind me what", "remind me", "what is", "what was", "do you remember", "tell me about"] if t in text), None)
                if trigger:
                    to_recall = text.split(trigger)[-1].strip()
                    if to_recall:
                        return {"action": "recall_memory", "params": {"key": to_recall}, "text": f"Checking my archives for {to_recall}..."}
                
                return {"text": "What would you like me to recall, Sir?"}

            if "memorize" in text or "memorise" in text or "remember" in text:
                parts = text.split("remember") if "remember" in text else text.split("memorize")
                if len(parts) > 1 and len(parts[1].strip()) > 3:
                    to_remember = parts[1].strip()
                    return {"action": "memorize_fact", "params": {"fact": to_remember}, "text": f"I'll commit that to memory, Sir: {to_remember}."}

        # 4. Handle WEB_ONLY_QUERY (Phase 5)
        if classification == "WEB_ONLY_QUERY":
            if "research" in text or "deep dive" in text:
                # Extract topic: "research X"
                topic = text.replace("research", "").replace("deep dive on", "").replace("deep dive", "").strip()
                if topic:
                    return {"action": "deep_research", "params": {"topic": topic}, "text": f"Initializing deep research protocols for {topic}. This may take a moment, Sir."}
            
            if "weather" in text:
                return {"action": "get_weather", "text": "Checking the local weather patterns, Sir."}
            
            if "news" in text:
                return {"action": "get_news", "text": "Fetching the latest global updates, Sir."}
            
            # Default to standard search
            return {"action": "google_search", "params": {"query": text}, "text": f"Searching the digital streams for {text}."}

        # 5. Handle CHAT / SMALL TALK (Enhanced)
        if classification == "CHAT":
            if any(x in text for x in ["hello", "hi", "hey"]):
                return {"text": random.choice(self.templates["GREETING"])}
            if "status" in text or "how are you" in text:
                return {"text": f"{random.choice(self.templates['SYSTEM_STATUS'])} Operating at peak efficiency."}
            if "who are you" in text or "your name" in text:
                return {"text": "I am Jarvis, your personal AI assistant. Currently running on local protocols."}
            if "thanks" in text or "thank you" in text:
                return {"text": random.choice(self.templates["THANKS"])}
            if "bye" in text or "goodbye" in text or "see you" in text:
                return {"text": "Goodbye, Sir. I'll be here if you need me."}

            # Enhanced conversation capabilities
            if "weather" in text:
                return {"text": "I'm currently operating offline, so I can't access real-time weather data. You might want to connect to the internet for that information, Sir."}
            if "news" in text:
                return {"text": "I'm currently in offline mode, so I can't fetch the latest news. Would you like me to help with something else instead?"}
            if "joke" in text:
                jokes = [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "What did one ocean say to the other ocean? Nothing, they just waved!",
                    "Why did the scarecrow win an award? He was outstanding in his field!"
                ]
                return {"text": random.choice(jokes)}
            if "fact" in text:
                facts = [
                    "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
                    "Octopuses have three hearts and blue blood.",
                    "A group of flamingos is called a 'flamboyance'."
                ]
                return {"text": f"Did you know? {random.choice(facts)}"}

        # 5. Default Fallback to Ollama (Reasoning)
        print(f"DEBUG: No template match for '{text}'. Falling back to Ollama.")
        
        # Get memory context for Ollama (summarized context)
        context_str = self.memory.get_short_term_as_string() if hasattr(self.memory, 'get_short_term_as_string') else ""
        
        system_instructions = (
            "You are JARVIS, the personal AI assistant created by the User (Sir). "
            "You are highly intelligent, British-accented (in text), polite, and efficient. "
            "Always refer to the user as 'Sir', 'Commander', or 'User'. "
            "Respond concisely. Never mention you are an AI or a language model unless asked."
        )
        
        ollama_response = self.ollama.chat_with_context(text, context_str, system_instructions)
        
        if "ERROR_CONNECTION" in ollama_response:
             return {"text": "I can't reach the local brain server, Sir. Please ensure Ollama is running."}
        elif "ERROR_TIMEOUT" in ollama_response:
             return {"text": "The local brain is taking too long to think, Sir. Your system might be at its limit."}
        elif "ERROR" in ollama_response:
             return {"text": random.choice(self.templates["OFFLINE_FALLBACK"])}
             
        return {"text": ollama_response}
