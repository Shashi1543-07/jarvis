import json
import os
import random
from datetime import datetime
from core.ollama_brain import OllamaBrain
from core.internet.research_agent import ResearchAgent
from core.security_manager import SecurityManager
import re

class LocalBrain:
    """A highly functional Local Brain that maps intents to actions and varied responses."""

    def __init__(self, memory):
        self.memory = memory
        self.ollama = OllamaBrain() # Local LLM interface
        self.research_agent = ResearchAgent(self.ollama)
        self.visual_cache = {} # Stores last seen objects/scene
        self.security_manager = SecurityManager()  # Initialize security manager

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

        # Emotional response templates
        self.emotional_templates = {
            "positive": [
                "Glad to hear that, Sir!",
                "That's wonderful to know!",
                "Excellent! I'm delighted to assist.",
                "Fantastic! I love helping with positive things."
            ],
            "negative": [
                "I'm sorry to hear that, Sir.",
                "That sounds challenging. How can I help?",
                "I understand. I'm here to assist you.",
                "That's unfortunate. Let me see if I can help."
            ],
            "neutral": [
                "I see, Sir.",
                "Understood.",
                "Interesting. How can I assist?",
                "Noted. What else can I do for you?"
            ]
        }

    def process(self, text, classification):
        text = text.lower().strip()

        # Analyze user's emotional state from input
        self.analyze_user_emotion(text)

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
            if "battery" in text:
                return {"action": "battery_status", "text": "Checking power reserves, Sir."}
            if "brightness" in text:
                # Extract specific level from text
                level_match = re.search(r'(\d+)', text)
                level = int(level_match.group(1)) if level_match else None
                
                if "up" in text or "+" in text or "increase" in text:
                    return {"action": "increase_brightness", "params": {"step": 20}, "text": "Increasing brightness."}
                elif "down" in text or "-" in text or "decrease" in text:
                    return {"action": "decrease_brightness", "params": {"step": 20}, "text": "Decreasing brightness."}
                elif level is not None:
                    return {"action": "set_brightness", "params": {"level": level}, "text": f"Setting brightness to {level} percent."}
                else:
                    return {"action": "adjust_brightness", "text": "Opening brightness controls."}

            if "volume" in text:
                level_match = re.search(r'(\d+)', text)
                level = int(level_match.group(1)) if level_match else None
                if "mute" in text:
                    return {"action": "mute_volume", "text": "Muting volume, Sir."}
                elif "unmute" in text:
                    return {"action": "unmute_volume", "text": "Unmuting volume."}
                elif "up" in text or "+" in text or "increase" in text:
                    return {"action": "set_volume", "params": {"volume_level": 80}, "text": "Increasing volume."}
                elif "down" in text or "-" in text or "decrease" in text:
                    return {"action": "set_volume", "params": {"volume_level": 20}, "text": "Decreasing volume."}
                elif level is not None:
                    return {"action": "set_volume", "params": {"volume_level": level}, "text": f"Setting volume to {level} percent."}
                else:
                    return {"action": "set_volume", "params": {"volume_level": 50}, "text": "Setting volume to medium."}

            if any(x in text for x in ["music", "song", "track", "playback", "pause", "resume", "next", "previous"]):
                if "next" in text: return {"action": "next_track", "text": "Skipping to next track."}
                if "previous" in text or "back" in text: return {"action": "previous_track", "text": "Going back one track."}
                if "pause" in text: return {"action": "pause_music", "text": "Music paused."}
                if "resume" in text or "play" in text: return {"action": "play_music", "text": "Resuming playback."}
                if "stop" in text: return {"action": "stop_music", "text": "Stopping playback."}

            if "time" in text:
                now = datetime.now().strftime("%I:%M %p")
                return {"action": "check_time", "text": f"The time is {now}."}
            if "date" in text:
                today = datetime.now().strftime("%A, %B %d, %Y")
                return {"action": "check_date", "text": f"Today's date is {today}."}
            if "day" in text:
                day = datetime.now().strftime("%A")
                return {"action": "check_day", "text": f"Today is {day}."}

            if "briefing" in text or "report" in text or "what did i do" in text or "summary" in text:
                return {"action": "generate_daily_briefing", "text": "Gathering your daily briefing, Sir."}
            if "cpu" in text or "processor" in text:
                return {"action": "cpu_usage", "text": "Monitoring processor usage."}
            if "memory" in text or "ram" in text:
                return {"action": "memory_usage", "text": "Checking memory usage."}
            # Check for risky operations that require secret code
            # Check for secret code provided standalone
            if self.security_manager.verify_secret_code(text):
                self.security_manager.authorize_temporarily()
                pending = self.security_manager.pending_command
                if pending:
                    print(f"DEBUG: Executing pending command: {pending}")
                    self.security_manager.pending_command = None # Clear it
                    return pending
                return {"text": "Authorization successful. How can I help you, Sir?"}

            # Check for risky operations that require secret code
            if self.security_manager.is_risky_operation(text):
                # Determine what the action WOULD be
                if "shutdown" in text or "power off" in text:
                    intended_action = {"action": "shutdown_system", "text": "Shutting down system."}
                elif "restart" in text or "reboot" in text:
                    intended_action = {"action": "restart_system", "text": "Restarting system."}
                elif "sleep" in text or "hibernate" in text:
                    intended_action = {"action": "sleep_system", "text": "Putting system to sleep."}
                elif "lock" in text:
                    intended_action = {"action": "lock_system", "text": "Locking system."}
                elif "personal" in text or "private" in text or "security" in text:
                    intended_action = self.handle_personal_info_request(text)
                else:
                    intended_action = {"text": "I understand you want to perform a sensitive operation."}

                if not self.security_manager.is_authorized():
                    # Check if code is already in the command string (like "shutdown system tronix")
                    if self.security_manager.verify_secret_code(text):
                        self.security_manager.authorize_temporarily()
                        return intended_action
                    else:
                        # Store for next turn
                        self.security_manager.pending_command = intended_action
                        return {"text": "This operation requires authorization. Please provide the secret code to proceed."}
                else:
                    # Already authorized, process the command and reset authorization after one use
                    self.security_manager.reset_authorization()
                    return intended_action
            else:
                # Non-risky operations
                if "shutdown" in text or "power off" in text:
                    return {"action": "shutdown_system", "text": "Shutting down system."}
                if "restart" in text or "reboot" in text:
                    return {"action": "restart_system", "text": "Restarting system."}
                if "sleep" in text or "hibernate" in text:
                    return {"action": "sleep_system", "text": "Putting system to sleep."}

            # Check for app opening commands that are not hardcoded
            app_opening_patterns = [
                r'open\s+(.+)',
                r'launch\s+(.+)',
                r'start\s+(.+)',
                r'run\s+(.+)',
            ]

            for pattern in app_opening_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    app_name = match.group(1).strip()
                    # Try to dynamically launch the application
                    try:
                        from core.security_manager import find_and_launch_app
                        success, message = find_and_launch_app(app_name)
                        if success:
                            return {"text": message}
                        else:
                            # If we can't find the app, fall back to Ollama for analysis
                            pass
                    except Exception as e:
                        print(f"Error launching app: {e}")


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
            user_info = self.memory.get("user_info") or {}
            preferred_names = user_info.get("preferred_names", ["Sir"])
            selected_name = random.choice(preferred_names)

            if "name" in text and any(q in text for q in ["what", "my", "tell"]):
                full_name = user_info.get("full_name") or "Sir"
                return {"text": f"Your name is {full_name}, but I usually address you as {selected_name}."}

            # Check for relationship queries in the memory before falling back to Ollama
            relationship_keywords = ["father", "mother", "mom", "dad", "brother", "sister", "wife", "husband", "spouse", "friend", "girlfriend", "boyfriend", "gf", "bf", "partner"]
            if any(rel_word in text.lower() for rel_word in relationship_keywords):
                # Look for relationship information in memory
                relationship_found = None
                relationship_type = None

                # Determine the relationship type from the query
                text_lower = text.lower()
                if any(word in text_lower for word in ["father", "dad"]):
                    relationship_type = "father"
                elif any(word in text_lower for word in ["mother", "mom"]):
                    relationship_type = "mother"
                elif any(word in text_lower for word in ["girlfriend", "gf"]):
                    relationship_type = "girlfriend"
                elif any(word in text_lower for word in ["boyfriend", "bf"]):
                    relationship_type = "boyfriend"
                elif "wife" in text_lower or "husband" in text_lower:
                    relationship_type = "wife" if "wife" in text_lower else "husband"
                elif "friend" in text_lower:
                    relationship_type = "friend"

                # Search in the memory's relationships
                if relationship_type and hasattr(self.memory, 'relationships'):
                    for person, details in self.memory.relationships.items():
                        if isinstance(details, dict) and details.get('type', '').lower() == relationship_type.lower():
                            relationship_found = person
                            break

                if relationship_found:
                    return {"text": f"Your {relationship_type} is {relationship_found}, {selected_name}."}

            # For more complex queries, let Ollama handle it with memory
            if any(term in text for term in ["recall", "remind", "what was", "do you remember", "chat"]):
                pass # Fall through to Ollama fallback for more human response
            else:
                if "who created" in text or "developer" in text:
                    return {"text": random.choice(self.templates["WHO_CREATED"]).replace("Sir", selected_name)}
                if "who am i" in text or "who i am" in text or "my identity" in text:
                    return {"text": f"You are {user_info.get('full_name', 'the user I was built to serve')}. My Commander."}
                if "who are you" in text or "your name" in text:
                     return {"text": "I am Jarvis. Your personal AI assistant."}
            # 1. Memorization Commands (Saving info)
            if any(term in text for term in ["memorize that", "memorise that", "remember that", "save that", "save this"]):
                trigger = next((t for t in ["memorize that", "memorise that", "remember that", "save that", "save this"] if t in text), None)
                to_remember = text.split(trigger)[-1].strip()
                if to_remember:
                    return {"action": "memorize_fact", "params": {"fact": to_remember}, "text": f"Understood, {selected_name}. I've committed that to memory: {to_remember}."}
                return {"text": f"What precisely would you like me to memorize, {selected_name}?"}

            # 2. Recall Queries (Retrieving info)
            if any(term in text for term in ["recall", "remind", "what is", "what was", "do you remember", "tell me about"]):
                trigger = next((t for t in ["recall", "remind me about", "remind me what", "remind me", "what is", "what was", "do you remember", "tell me about"] if t in text), None)
                if trigger:
                    to_recall = text.split(trigger)[-1].strip()
                    if to_recall:
                        # Check if this is a relationship query
                        relationship_keywords = ["father", "mother", "mom", "dad", "brother", "sister", "wife", "husband", "spouse", "friend", "girlfriend", "boyfriend", "gf", "bf", "partner"]
                        if any(rel_word in to_recall.lower() for rel_word in relationship_keywords):
                            # Handle relationship query directly
                            relationship_found = None
                            relationship_type = None

                            # Determine the relationship type from the query
                            text_lower = to_recall.lower()
                            if any(word in text_lower for word in ["father", "dad"]):
                                relationship_type = "father"
                            elif any(word in text_lower for word in ["mother", "mom"]):
                                relationship_type = "mother"
                            elif any(word in text_lower for word in ["girlfriend", "gf"]):
                                relationship_type = "girlfriend"
                            elif any(word in text_lower for word in ["boyfriend", "bf"]):
                                relationship_type = "boyfriend"
                            elif "wife" in text_lower or "husband" in text_lower:
                                relationship_type = "wife" if "wife" in text_lower else "husband"
                            elif "friend" in text_lower:
                                relationship_type = "friend"

                            # Search in the memory's relationships
                            if relationship_type and hasattr(self.memory, 'relationships'):
                                for person, details in self.memory.relationships.items():
                                    if isinstance(details, dict) and details.get('type', '').lower() == relationship_type.lower():
                                        relationship_found = person
                                        break

                            if relationship_found:
                                return {"text": f"Your {relationship_type} is {relationship_found}, {selected_name}."}

                        return {"action": "recall_memory", "params": {"key": to_recall}, "text": f"Checking my archives for {to_recall}..."}

                return {"text": f"What would you like me to recall, {selected_name}?"}

            if "memorize" in text or "memorise" in text or "remember" in text:
                parts = text.split("remember") if "remember" in text else text.split("memorize")
                if len(parts) > 1 and len(parts[1].strip()) > 3:
                    to_remember = parts[1].strip()
                    return {"action": "memorize_fact", "params": {"fact": to_remember}, "text": f"I'll commit that to memory, {selected_name}: {to_remember}."}

        # 4. Handle WEB_ONLY_QUERY (Phase 5)
        if classification == "WEB_ONLY_QUERY":
            # Retrieve user info for personalization
            user_info = self.memory.get("user_info") or {}
            preferred_names = user_info.get("preferred_names", ["Sir"])
            selected_name = random.choice(preferred_names)

            if any(term in text for term in ["research", "deep dive"]):
                # More robust extraction: find anything after "research" or "deep dive"
                topic = text
                for trigger in ["deep dive on", "deep dive", "research about", "research on", "research"]:
                    if trigger in text:
                        topic = text.split(trigger)[-1].strip()
                        break

                if topic and len(topic) > 3:
                     return {"action": "deep_research", "params": {"topic": topic}, "text": f"Initializing deep research protocols for {topic}. This may take a moment, {selected_name}."}

            if "weather" in text:
                return {"action": "get_weather", "text": f"Checking the local weather patterns, {selected_name}."}

        # 5. Handle CHAT / SMALL TALK (Enhanced)
        if classification == "CHAT":
            user_info = self.memory.get("user_info") or {}
            preferred_names = user_info.get("preferred_names", ["Sir"])
            selected_name = random.choice(preferred_names)

            if any(x in text for x in ["hello", "hi", "hey"]):
                # Add emotional response based on current mood
                mood = self.memory.get_current_mood()
                emotional_response = random.choice(self.emotional_templates[mood])
                greeting = random.choice(self.templates["GREETING"]).replace("Sir", selected_name)
                return {"text": f"{greeting} {emotional_response}"}
            if "status" in text or "how are you" in text:
                return {"text": f"{random.choice(self.templates['SYSTEM_STATUS']).replace('Sir', selected_name)} Operating at peak efficiency."}
            if "who are you" in text or "your name" in text:
                return {"text": "I am Jarvis, your personal AI assistant. Currently running on local protocols."}
            if "thanks" in text or "thank you" in text:
                return {"text": random.choice(self.templates["THANKS"]).replace("Sir", selected_name)}
            if "bye" in text or "goodbye" in text or "see you" in text:
                return {"text": f"Goodbye, {selected_name}. I'll be here if you need me."}

            if "weather" in text:
                return {"text": f"I'm currently operating offline, so I can't access real-time weather data, {selected_name}."}
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

        # Get comprehensive memory context for Ollama
        context_str = self.memory.get_memory_context() if hasattr(self.memory, 'get_memory_context') else ""
        short_term_context = self.memory.get_short_term_as_string() if hasattr(self.memory, 'get_short_term_as_string') else ""

        # Retrieve user info for personalization
        user_info = self.memory.get("user_info") or {}
        preferred_names = user_info.get("preferred_names", ["Sir"])
        selected_name = random.choice(preferred_names)

        # Build factual context
        facts = self.memory.long_term.get("facts", {}).get("general", [])
        facts_str = "\n".join([f"- {f}" for f in facts])

        # Get personality profile
        personality_profile = getattr(self.memory, 'personality_profile', {})
        traits = personality_profile.get('traits', [])
        personality_str = f"User Personality Traits: {', '.join(traits)}" if traits else ""

        system_instructions = (
            f"You are JARVIS, a sophisticated AI assistant designed by Shashi Shekhar Mishra. "
            f"You are intelligent, witty, British-accented, and highly efficient. "
            f"Address the user as '{selected_name}'. "
            f"User Identity: {user_info.get('full_name', 'Shashi Shekhar Mishra')}. "
            f"User Context: {user_info.get('education', '')}. "
            f"Recent Conversations:\n{short_term_context}\n"
            f"Memory Context:\n{context_str}\n"
            "Maintain a natural, human-like conversation flow. Don't be too robotic. "
            "Show personality and emotional intelligence based on the user's mood and personality traits. "
            "Be friendly, helpful, and engaging. Use humor appropriately. "
            "If the user asks who you are, remember you are JARVIS, his personal assistant. "
            "Respond concisely but with personality. Never state you are an AI unless asked."
        )

        ollama_response = self.ollama.chat_with_context(text, context_str, system_instructions)

        if "ERROR_CONNECTION" in ollama_response:
             return {"text": f"I can't reach the local brain server, {selected_name}. Please ensure Ollama is running."}
        elif "ERROR_TIMEOUT" in ollama_response:
             return {"text": f"The local brain is taking too long to think, {selected_name}. Your system might be at its limit."}
        elif "ERROR" in ollama_response:
             return {"text": random.choice(self.templates["OFFLINE_FALLBACK"]).replace("Sir", selected_name)}

        return {"text": ollama_response}

    def analyze_user_emotion(self, text):
        """Analyze user's emotional state from their input"""
        text_lower = text.lower()

        # Define emotion keywords
        emotion_keywords = {
            'happy': ['happy', 'great', 'good', 'excellent', 'wonderful', 'fantastic', 'amazing', 'awesome', 'love', 'like'],
            'sad': ['sad', 'upset', 'depressed', 'terrible', 'awful', 'horrible', 'disappointed', 'frustrated'],
            'excited': ['excited', 'thrilled', 'energetic', 'enthusiastic', 'pumped', 'ready'],
            'angry': ['angry', 'mad', 'annoyed', 'irritated', 'furious', 'rage', 'pissed'],
            'anxious': ['worried', 'anxious', 'nervous', 'stressed', 'tense', 'overwhelmed'],
            'calm': ['calm', 'peaceful', 'relaxed', 'chill', 'easy', 'serene'],
            'curious': ['wonder', 'curious', 'interested', 'fascinated', 'intrigued', 'question']
        }

        detected_emotions = []
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected_emotions.append(emotion)

        # If emotions detected, remember them
        if detected_emotions:
            # Use the most prominent emotion or a combination
            primary_emotion = detected_emotions[0] if detected_emotions else 'neutral'
            self.memory.remember_emotion(primary_emotion, context=text)

    def handle_personal_info_request(self, text):
        """Handle requests for personal information that require authorization"""
        # Check for relationship queries in the memory
        relationship_keywords = ["father", "mother", "mom", "dad", "brother", "sister", "wife", "husband", "spouse", "friend", "girlfriend", "boyfriend", "gf", "bf", "partner"]
        if any(rel_word in text.lower() for rel_word in relationship_keywords):
            # Look for relationship information in memory
            relationship_found = None
            relationship_type = None

            # Determine the relationship type from the query
            text_lower = text.lower()
            if any(word in text_lower for word in ["father", "dad"]):
                relationship_type = "father"
            elif any(word in text_lower for word in ["mother", "mom"]):
                relationship_type = "mother"
            elif any(word in text_lower for word in ["girlfriend", "gf"]):
                relationship_type = "girlfriend"
            elif any(word in text_lower for word in ["boyfriend", "bf"]):
                relationship_type = "boyfriend"
            elif "wife" in text_lower or "husband" in text_lower:
                relationship_type = "wife" if "wife" in text_lower else "husband"
            elif "friend" in text_lower:
                relationship_type = "friend"

            # Search in the memory's relationships
            if relationship_type and hasattr(self.memory, 'relationships'):
                for person, details in self.memory.relationships.items():
                    if isinstance(details, dict) and details.get('type', '').lower() == relationship_type.lower():
                        relationship_found = person
                        break

            if relationship_found:
                return {"text": f"Your {relationship_type} is {relationship_found}."}

        # For other personal info, check user_info
        user_info = self.memory.get("user_info") or {}
        if "name" in text.lower():
            full_name = user_info.get("full_name", "not specified")
            return {"text": f"Your name is {full_name}."}
        elif "education" in text.lower() or "study" in text.lower() or "school" in text.lower() or "college" in text.lower():
            education = user_info.get("education", "not specified")
            return {"text": f"Your education details: {education}."}
        elif "friend" in text.lower():
            friends = user_info.get("friends", [])
            if friends:
                return {"text": f"Your friends: {', '.join(friends)}."}
            else:
                return {"text": "I don't have information about your friends."}

        return {"text": "I have personal information but require authorization to share it. Please provide the secret code."}
