import json
import os
import random
from datetime import datetime
from .ollama_brain import OllamaBrain
from .internet.research_agent import ResearchAgent
from .security_manager import SecurityManager
import re

class MemoryAuthority:
    """Deterministic memory lookups - NO LLM hallucination allowed."""
    
    # Factual query patterns that MUST use memory, not LLM
    FACTUAL_PATTERNS = [
        r"who is my (\w+)",
        r"what is my (\w+)(?:'s name)?",
        r"do you (know|remember) (?:who|what) (?:is )?my (\w+)",
        r"tell me who (?:is )?my (\w+)",
        r"who(?:'s| is) my (\w+)"
    ]
    
    # Memory write patterns (explicit confirmation only)
    MEMORY_WRITE_PATTERNS = [
        r"remember (?:that )?my (\w+) is ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"my (\w+) is ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"note that my (\w+)(?:'s name)? is ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"memorize (?:that )?my (\w+) is ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
    ]
    
    def is_factual_query(self, text):
        """Check if query demands deterministic memory lookup."""
        for pattern in self.FACTUAL_PATTERNS:
            if re.search(pattern, text.lower()):
                return True
        return False
    
    def extract_relationship_type(self, text):
        """Extract relationship type from factual query."""
        for pattern in self.FACTUAL_PATTERNS:
            match = re.search(pattern, text.lower())
            if match:
                # Get the last captured group (relationship type)
                return match.group(match.lastindex)
        return None
    
    def lookup_relationship(self, rel_type, memory):
        """Query memory for relationship. Return (person_name, confidence) or None."""
        if hasattr(memory, 'relationships'):
            for person, details in memory.relationships.items():
                if isinstance(details, dict):
                    stored_type = details.get('type', '').lower()
                    if stored_type == rel_type.lower():
                        confidence = details.get('confidence', 1.0)
                        return (person, confidence)
        return None
    
    def detect_memory_write(self, text):
        """Detect explicit memory write command. Return (rel_type, person) or None."""
        for pattern in self.MEMORY_WRITE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    rel_type, person_name = groups[-2], groups[-1]
                    return (rel_type.lower(), person_name)
        return None

class LocalBrain:
    """A highly functional Local Brain that maps intents to actions and varied responses."""

    def __init__(self, memory):
        self.memory = memory
        self.ollama = OllamaBrain() # Local LLM interface
        self.research_agent = ResearchAgent(self.ollama)
        self.visual_cache = {} # Stores last seen objects/scene
        self.security_manager = SecurityManager()  # Initialize security manager
        # Initialize NLU Engine
        from .nlu.engine import NLUEngine
        from .nlu.intents import IntentType
        self.nlu = NLUEngine(self.ollama)
        self.memory_authority = MemoryAuthority()  # Memory authority layer

        # Jarvis-style conversational templates (Friendly & Varied)
        # TRIPLED variety to prevent repetition
        self.templates = {
            "GREETING": [
                "Hey there! What can I do for you?",
                "Good to see you! How can I help?",
                "Hello! Ready when you are.",
                "What's up? I'm all ears.",
                "At your service! What's on your mind?",
                "Hey! Got something for me?",
                "Welcome back! What are we working on?",
                "Here and ready! Fire away.",
                "I'm listening. What do you need?",
                "Hey hey! What's the plan?",
                "Standing by and attentive!",
                "Right here! What can I help with?",
            ],
            "THANKS": [
                "Happy to help!",
                "Anytime!",
                "Of course!",
                "My pleasure!",
                "No problem at all!",
                "Glad I could help!",
                "That's what I'm here for!",
                "You got it!",
                "Sure thing!",
                "Always!",
                "Don't mention it!",
                "Absolutely!",
            ],
            "WHO_CREATED": [
                "I was designed by you, to be the ultimate assistant.",
                "You're my creator! I'm a product of your engineering.",
                "Built by you, for you.",
                "I'm your creation - designed to help.",
            ],
            "OFFLINE_FALLBACK": [
                "I'm handling this locally for speed.",
                "Processing offline for efficiency.",
                "Running on local protocols.",
                "Using local processing right now.",
                "Handling this on-device.",
            ],
            "NOT_UNDERSTOOD": [
                "Hmm, I didn't quite catch that. Could you rephrase?",
                "I'm not sure I understood. Mind saying that differently?",
                "That one went over my head. Try again?",
                "Sorry, I missed that. What did you mean?",
            ],
            "SYSTEM_STATUS": [
                "All systems good!",
                "Everything's running smoothly.",
                "Systems are green across the board.",
                "All nominal here!",
                "Running at full capacity!",
            ],
            "ACKNOWLEDGEMENT": [
                "Got it!",
                "On it!",
                "Consider it done.",
                "Right away!",
                "Working on it!",
                "One moment...",
                "Let me handle that.",
                "Coming right up!",
            ]
        }

        # Emotional response templates (expanded variety)
        self.emotional_templates = {
            "positive": [
                "That's great to hear!",
                "Wonderful!",
                "Excellent!",
                "Love that energy!",
                "Fantastic!",
                "Nice!",
            ],
            "negative": [
                "I'm sorry to hear that.",
                "That sounds tough.",
                "I understand. How can I help?",
                "That's rough. Let me see what I can do.",
            ],
            "neutral": [
                "I see.",
                "Understood.",
                "Got it.",
                "Noted.",
                "Alright.",
            ]
        }
        
        # ANTI-REPETITION: Track recently used responses per category
        self.recent_responses = {}  # category -> list of recent texts
        self.response_history_size = 5  # Don't repeat within last N responses

    def _old_process_deprecated(self, text, classification):
        """
        NOTE: This method has been replaced by generate_chat_response().
        The old NLU parsing logic is now handled by Router's unified IntentClassifier.
        This stub is kept only for reference - will be removed in future.
        """
        pass
    
    def _get_unique_response(self, category: str, name_replacement: str = None) -> str:
        """
        Get a response from category that hasn't been used recently.
        Prevents repetitive greetings/acknowledgements.
        
        Args:
            category: Template category key (e.g., "GREETING", "THANKS")
            name_replacement: Optional name to replace "Sir" with
            
        Returns:
            A response string that hasn't been used in last N responses
        """
        templates = self.templates.get(category, [""])
        
        # Get recent responses for this category
        recent = self.recent_responses.get(category, [])
        
        # Find responses not recently used
        available = [t for t in templates if t not in recent]
        
        # If all used recently, use any (but prefer least recent)
        if not available:
            available = templates
            # Clear history to allow reuse
            self.recent_responses[category] = []
        
        # Pick random from available
        response = random.choice(available)
        
        # Track this response
        if category not in self.recent_responses:
            self.recent_responses[category] = []
        self.recent_responses[category].append(response)
        
        # Keep history limited
        if len(self.recent_responses[category]) > self.response_history_size:
            self.recent_responses[category].pop(0)
        
        # Apply name replacement if needed
        if name_replacement:
            response = response.replace("Sir", name_replacement)
        
        return response

    def generate_chat_response(self, text: str) -> dict:
        """
        Generate a pure conversational response via templates or Ollama LLM.
        This is the primary method for handling CONVERSATION/CHAT intents.
        
        Args:
            text: User's input text
            
        Returns:
            dict with 'text' key containing the response
        """
        text_lower = text.lower().strip()
        
        # Handle FILLERS (Quiet acknowledgement or silence)
        fillers = ["mmm", "hmm", "okay", "uh", "ah", "yep", "yup", "got it", "nice"]
        if text_lower in fillers or len(text_lower) < 3:
            return {"text": ""} 

        # Analyze user's emotional state from input
        self.analyze_user_emotion(text_lower)
        
        # Retrieve user info for personalization
        user_info = self.memory.get("user_info") or {}
        preferred_names = user_info.get("preferred_names", [""])
        selected_name = random.choice(preferred_names) if preferred_names else ""

        # Template handling for greetings (with anti-repetition)
        if any(x in text_lower for x in ["hello", "hi", "hey"]) and len(text_lower.split()) < 3:
            greeting = self._get_unique_response("GREETING", selected_name)
            return {"text": greeting}
            
        # Template handling for thanks (with anti-repetition)
        if "thanks" in text_lower or "thank you" in text_lower:
            thanks = self._get_unique_response("THANKS", selected_name)
            return {"text": thanks}

        # Default Fallback to Ollama (Guarded & Grounded)
        context_str = self.memory.get_memory_context() if hasattr(self.memory, 'get_memory_context') else ""
        short_term_context = self.memory.get_short_term_as_string() if hasattr(self.memory, 'get_short_term_as_string') else ""

        system_instructions = (
            f"You are JARVIS, an advanced, sentient personal assistant with a sharp, witty, and human-like personality. "
            f"Address the user as '{selected_name}'. "
            f"User Identity: {user_info.get('full_name', 'Shashi Shekhar Mishra')}. "
            "TONE: Energetic, witty, and deeply loyal. Sound like a genius companion, not a computer. "
            "RULES:\n"
            "1. NO REPETITION. Never repeat the user's input or say 'At your service' every turn.\n"
            "2. BE NATURAL. Use contractions (I'll, you're, won't). Avoid 'Sir, I have...'. Say 'I've got that for you, Sir.'\n"
            "3. BE PROACTIVE. If you detect a context like work or study, offer help.\n"
            "4. VARIETY. Use diverse sentence structures. Don't start every message with the user's name.\n"
            "5. NO SCRIPTED SPEECH. Talk like you're thinking. If a task takes time, acknowledge it wittily.\n"
            f"\nRecent Conversation History:\n{short_term_context}\n"
            f"Memory Context:\n{context_str}\n"
            "CRITICAL: Be concise but vibrant. NO flowery robotic greetings. Plain text ONLY."
        )

        ollama_response = self.ollama.chat_with_context(text, context_str, system_instructions)

        if "ERROR_CONNECTION" in ollama_response:
             return {"text": f"I can't reach the local brain server, {selected_name}. Please ensure Ollama is running."}
        elif "ERROR_TIMEOUT" in ollama_response:
             return {"text": f"The local brain is taking too long to think, {selected_name}. Your system might be at its limit."}
        elif "ERROR" in ollama_response:
             return {"text": random.choice(self.templates["OFFLINE_FALLBACK"]).replace("Sir", selected_name)}

        return {"text": ollama_response}

    def process(self, text, classification):
        """
        DEPRECATED: Use Router's unified classification instead.
        This method is kept for backward compatibility only.
        
        New code should call generate_chat_response() directly for conversational responses.
        """
        import warnings
        warnings.warn(
            "LocalBrain.process() is deprecated. Use Router for intent routing, "
            "and LocalBrain.generate_chat_response() for chat.",
            DeprecationWarning, 
            stacklevel=2
        )
        return self.generate_chat_response(text)

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
