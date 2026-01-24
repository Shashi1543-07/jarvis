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
        original_text = text  # Keep original for memory writes
        text = text.lower().strip()  # Normalize text for pattern matching
        
        # ═══════════════════════════════════════════════════════════
        # PHASE B: INTENT CLASSIFICATION (NLU ENGINE)
        # ═══════════════════════════════════════════════════════════
        
        # Use NLU Engine to parse intent
        intent = self.nlu.parse(original_text)
        
        from .nlu.intents import IntentType
        
        # If it's a specific system intent, return the Intent Object (as dict)
        if intent.intent_type not in [IntentType.CONVERSATION, IntentType.UNKNOWN, IntentType.CLARIFICATION_REQUIRED]:
            return intent.to_dict()

        if intent.intent_type == IntentType.CLARIFICATION_REQUIRED:
            return {"text": intent.clarification_question or "Could you clarify that, Sir?"}

        # ═══════════════════════════════════════════════════════════
        # PHASE C: CONVERSATIONAL FALLBACK (TEMPLATES / CHAT LLM)
        # ═══════════════════════════════════════════════════════════
        
        # 0. Handle FILLERS (Quiet acknowledgement or silence)
        fillers = ["mmm", "hmm", "okay", "uh", "ah", "yep", "yup", "got it", "nice"]
        if text in fillers or len(text) < 3:
            return {"text": ""} 

        # Analyze user's emotional state from input
        self.analyze_user_emotion(text)
        
        # Retrieve user info for personalization
        user_info = self.memory.get("user_info") or {}
        preferred_names = user_info.get("preferred_names", ["Sir"])
        selected_name = random.choice(preferred_names)

        # Template handling for greetings/thanks
        if any(x in text for x in ["hello", "hi", "hey"]) and len(text.split()) < 3:
            mood = self.memory.get_current_mood()
            emotional_response = random.choice(self.emotional_templates[mood])
            greeting = random.choice(self.templates["GREETING"]).replace("Sir", selected_name)
            return {"text": f"{greeting} {emotional_response}"}
            
        if "thanks" in text or "thank you" in text:
            return {"text": random.choice(self.templates["THANKS"]).replace("Sir", selected_name)}

        # Default Fallback to Ollama (Guarded & Grounded)
        # Get comprehensive memory context for Ollama
        context_str = self.memory.get_memory_context() if hasattr(self.memory, 'get_memory_context') else ""
        short_term_context = self.memory.get_short_term_as_string() if hasattr(self.memory, 'get_short_term_as_string') else ""

        system_instructions = (
            f"You are JARVIS, a sophisticated and grounded personal assistant designed by Shashi Shekhar Mishra. "
            f"Address the user as '{selected_name}'. "
            f"User Identity: {user_info.get('full_name', 'Shashi Shekhar Mishra')}. "
            f"Tone: Intelligent, concise, professional, and slightly witty (British). "
            f"Behavior: Answer the user's request directly. If they ask for a joke, tell a short one. "
            f"If you don't have the information in your Memory Context, admit you don't know it yet. "
            f"Recent Highlights:\n{short_term_context}\n"
            f"Memory Context:\n{context_str}\n"
            "CRITICAL: Be concise. No flowery greetings if replying to a mid-conversation query. "
            "Plain text ONLY. No JSON."
        )

        ollama_response = self.ollama.chat_with_context(original_text, context_str, system_instructions)

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
