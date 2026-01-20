import json
import os
import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from collections import defaultdict
import re

class EnhancedMemory:
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.memory_file = os.path.join(self.config_dir, 'memory.json')

        # Core memory structures (Layered)
        self.working_memory = []  # ENTITIES/TOPICS in current 15s window
        self.short_term = []      # Last 10 conversation turns - cleared on exit
        self.episodic_memory = [] # Session summaries and life events
        self.semantic_memory = {} # VERIFIED FACTS: {subject: {fact_list: [{fact, confidence, confirmed}]}}

        self.long_term = {}  # Legacy key-value storage
        self.sessions = []   # Legacy session history
        self.tasks = {}      # Ongoing tasks

        # Enhanced memory structures
        self.emotions = []
        self.personality_profile = {}
        self.relationships = {} 
        self.interests = set()
        self.favorites = {}
        self.personal_history = [] 
        self.temporary_context = [] 

        # Write-Block Patterns (Do not store if user asks these)
        self.BLOCK_PATTERNS = [
            r"^(who|what|where|when|why|how|can you|do you|is there|is my|tell me|recall|remind)",
            r"\b(maybe|perhaps|probably|i think|not sure|guess|assume|might)\b"
        ]

        # Embeddings cache (optional, loaded on demand)
        self.embeddings_model = None
        self.memory_embeddings = []
        self.memory_texts = []

        self.load_memory()

    def load_memory(self):
        """Load all memory from persistent storage"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.long_term = data.get('long_term', {})
                    self.short_term = data.get('short_term', [])
                    self.sessions = data.get('sessions', [])
                    self.tasks = data.get('tasks', {})
                    
                    # New Layered Structures
                    self.working_memory = data.get('working_memory', [])
                    self.episodic_memory = data.get('episodic_memory', [])
                    self.semantic_memory = data.get('semantic_memory', {})

                    # Load enhanced memory structures
                    self.emotions = data.get('emotions', [])
                    self.personality_profile = data.get('personality_profile', {})
                    self.conversation_patterns = data.get('conversation_patterns', {})
                    self.relationships = data.get('relationships', {})
                    self.habits = data.get('habits', {})
                    self.interests = set(data.get('interests', []))
                    self.favorites = data.get('favorites', {})
                    self.personal_history = data.get('personal_history', [])
            else:
                self.long_term = {}
                self.short_term = []
                self.sessions = []
                self.tasks = {}
                
                # Initialize enhanced memory structures
                self.emotions = []
                self.personality_profile = {}
                self.conversation_patterns = {}
                self.relationships = {}
                self.habits = {}
                self.interests = set()
                self.favorites = {}
                self.personal_history = []
            print("Enhanced Memory: Loaded.")
        except Exception as e:
            print(f"Enhanced Memory: Failed to load: {e}")
            self.long_term = {}
            self.short_term = []
            self.sessions = []
            self.tasks = {}
            
            # Initialize enhanced memory structures
            self.emotions = []
            self.personality_profile = {}
            self.conversation_patterns = {}
            self.relationships = {}
            self.habits = {}
            self.interests = set()
            self.favorites = {}
            self.personal_history = []

    def save_memory(self):
        """Save all memory to persistent storage"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            data = {
                'long_term': self.long_term,
                'short_term': self.short_term,
                'sessions': self.sessions,
                'tasks': self.tasks,
                'working_memory': self.working_memory,
                'episodic_memory': self.episodic_memory,
                'semantic_memory': self.semantic_memory,
                
                # Save enhanced memory structures
                'emotions': self.emotions,
                'personality_profile': self.personality_profile,
                'conversation_patterns': self.conversation_patterns,
                'relationships': self.relationships,
                'habits': self.habits,
                'interests': list(self.interests),
                'favorites': self.favorites,
                'personal_history': self.personal_history
            }
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("Enhanced Memory: Saved.")
        except Exception as e:
            print(f"Enhanced Memory: Failed to save: {e}")

    # ===== Basic Key-Value Storage =====

    def get(self, key):
        """Get a value from long-term memory"""
        return self.long_term.get(key)

    def set(self, key, value):
        """Set a value in long-term memory"""
        self.long_term[key] = value
        self.save_memory()

    # ===== Enhanced Memory Features =====

    def remember_emotion(self, emotion, intensity=1, context=""):
        """Remember user's emotional state"""
        emotion_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'emotion': emotion,
            'intensity': intensity,
            'context': context
        }
        self.emotions.append(emotion_entry)
        
        # Keep only last 50 emotion entries
        if len(self.emotions) > 50:
            self.emotions = self.emotions[-50:]
        
        self.save_memory()

    def get_current_mood(self):
        """Get user's current mood based on recent emotions"""
        if not self.emotions:
            return "neutral"
        
        recent_emotions = self.emotions[-10:]  # Last 10 emotions
        positive_count = sum(1 for e in recent_emotions if e['emotion'] in ['happy', 'excited', 'joyful', 'content'])
        negative_count = sum(1 for e in recent_emotions if e['emotion'] in ['sad', 'angry', 'frustrated', 'anxious'])
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"

    def remember_interest(self, interest):
        """Remember user's interests"""
        self.interests.add(interest.lower())
        self.save_memory()

    def remember_favorite(self, category, item):
        """Remember user's favorites"""
        if category not in self.favorites:
            self.favorites[category] = []
        if item not in self.favorites[category]:
            self.favorites[category].append(item)
        self.save_memory()

    def remember_habit(self, habit, frequency="daily"):
        """Remember user's habits"""
        self.habits[habit] = {
            'frequency': frequency,
            'last_recorded': datetime.datetime.now().isoformat()
        }
        self.save_memory()

    def remember_contact_info(self, contact_type, contact_value):
        """Remember contact information like email, phone, address"""
        if 'contact_info' not in self.long_term:
            self.long_term['contact_info'] = {}
        if contact_type not in self.long_term['contact_info']:
            self.long_term['contact_info'][contact_type] = []

        # Add new contact info if it's not already stored
        if isinstance(contact_value, list):
            for item in contact_value:
                if item not in self.long_term['contact_info'][contact_type]:
                    self.long_term['contact_info'][contact_type].append(item)
        else:
            if contact_value not in self.long_term['contact_info'][contact_type]:
                self.long_term['contact_info'][contact_type].append(contact_value)

        self.save_memory()

    def remember_relationship(self, person, relationship_type, details="", source="manual", confidence=0.8):
        """Remember personal relationships"""
        self.relationships[person] = {
            'type': relationship_type,
            'details': details,
            'source': source,
            'confidence': confidence,
            'timestamp': datetime.datetime.now().isoformat(),
            'last_interaction': datetime.datetime.now().isoformat()
        }
        self.save_memory()

    def remember_personal_event(self, event_type, description, date=None):
        """Remember important personal events"""
        event = {
            'type': event_type,
            'description': description,
            'date': date or datetime.datetime.now().isoformat()
        }
        self.personal_history.append(event)
        
        # Keep only last 20 events
        if len(self.personal_history) > 20:
            self.personal_history = self.personal_history[-20:]
        
        self.save_memory()

    def analyze_personality(self):
        """Analyze user's personality based on interactions"""
        if not self.emotions:
            return {"traits": [], "confidence": 0}
        
        # Analyze emotional patterns
        emotions_by_type = defaultdict(list)
        for emotion in self.emotions:
            emotions_by_type[emotion['emotion']].append(emotion['intensity'])
        
        # Determine personality traits based on emotional patterns
        traits = []
        if any(k in emotions_by_type for k in ['happy', 'excited', 'joyful']):
            traits.append("optimistic")
        if any(k in emotions_by_type for k in ['calm', 'peaceful', 'content']):
            traits.append("calm")
        if any(k in emotions_by_type for k in ['curious', 'interested']):
            traits.append("curious")
        if any(k in emotions_by_type for k in ['focused', 'determined']):
            traits.append("determined")
        
        # Update personality profile
        self.personality_profile = {
            'traits': traits,
            'emotional_tendency': self.get_current_mood(),
            'last_analysis': datetime.datetime.now().isoformat()
        }
        
        self.save_memory()
        return self.personality_profile

    def detect_conversation_pattern(self, user_input, ai_response):
        """Detect conversation patterns"""
        # Simple pattern detection
        if user_input.lower().startswith(('how', 'what', 'when', 'where', 'why')):
            pattern = 'question'
        elif user_input.lower().endswith(('.', '!', '?')):
            pattern = 'statement'
        elif user_input.lower().endswith((',', ';')):
            pattern = 'continuation'
        else:
            pattern = 'other'
        
        if pattern not in self.conversation_patterns:
            self.conversation_patterns[pattern] = 0
        self.conversation_patterns[pattern] += 1
        
        self.save_memory()

    def remember_context(self, text):
        """Add to short-term conversation memory"""
        self.short_term.append(text)
        if len(self.short_term) > 10:  # Keep last 10 interactions
            self.short_term.pop(0)
        self.save_memory() # Auto-save context

    def remember_conversation(self, user_input, ai_response):
        """Main entry point for storing conversation turns across memory layers."""
        # 1. Update Working Memory (Entities/Pronouns window)
        self.update_working_memory(user_input)

        # 2. Add to Short Term (Conversation stream)
        conversation_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'user': user_input,
            'ai': ai_response,
            'mood': self.get_current_mood()
        }
        self.short_term.append(conversation_entry)
        if len(self.short_term) > 10:
            self.short_term.pop(0)

        # 3. Process for Semantic Memory (Factual commit - with strict blockers)
        if not self.should_block_semantic_write(user_input):
            self.process_conversation_for_memory(user_input, ai_response)

        self.save_memory()
        self.detect_conversation_pattern(user_input, ai_response)
        self.extract_interests_from_conversation(user_input)

    def update_working_memory(self, text):
        """ prunes and updates entities for pronoun resolution (15s TTL) """
        now = datetime.datetime.now()
        # Prune expired (older than 15s)
        self.working_memory = [m for m in self.working_memory 
                              if (now - datetime.datetime.fromisoformat(m['timestamp'])).total_seconds() < 15]
        
        # Simple entity extraction (Capitalized words or specific patterns)
        entities = re.findall(r'\b[A-Z][a-z]+\b', text)
        for ent in entities:
            if ent not in ["I", "Jarvis"]:
                self.working_memory.append({
                    'entity': ent,
                    'timestamp': now.isoformat()
                })

    def should_block_semantic_write(self, text):
        """ BLOCK if it's a question or uncertain """
        text_lower = text.lower().strip()
        for pattern in self.BLOCK_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def remember_semantic_fact(self, subject, fact_text, confidence=0.4, confirmed=False):
        """ Store facts with confidence levels """
        subject = subject.lower()
        if subject not in self.semantic_memory:
            self.semantic_memory[subject] = []
        
        # Check for existing similar fact
        exists = False
        for f in self.semantic_memory[subject]:
            if f['fact'].lower() == fact_text.lower():
                f['mentions'] = f.get('mentions', 1) + 1
                f['confidence'] = min(1.0, f['confidence'] + 0.2)
                if confirmed: f['confirmed'] = True
                f['last_seen'] = datetime.datetime.now().isoformat()
                exists = True
                break
        
        if not exists:
            self.semantic_memory[subject].append({
                'fact': fact_text,
                'confidence': 1.0 if confirmed else confidence,
                'confirmed': confirmed,
                'mentions': 1,
                'last_seen': datetime.datetime.now().isoformat()
            })
        
        print(f"Semantic Memory: Updated {subject} -> {fact_text}")

    def extract_interests_from_conversation(self, user_input):
        """Extract interests from user input"""
        # Look for keywords indicating interests
        interest_keywords = [
            'love', 'like', 'enjoy', 'favorite', 'prefer', 'interested in',
            'passionate about', 'hobby', 'interest', 'fascinated by'
        ]

        user_lower = user_input.lower()
        for keyword in interest_keywords:
            if keyword in user_lower:
                # Extract the interest mentioned after the keyword
                parts = user_input.split(keyword)
                if len(parts) > 1:
                    interest = parts[1].strip().split()[0] if parts[1].strip().split() else ""
                    if interest:
                        self.remember_interest(interest)

    def classify_conversation_content(self, user_input, ai_response=""):
        """
        Classify conversation content as general command or important personal information
        Returns: ('general', 'command') or ('important', 'category')
        """
        # Define patterns for general commands
        general_patterns = [
            r'\b(open|launch|start)\s+\w+',  # open calculator, launch app
            r'\b(play|stop|pause)\s+(music|song|video)',  # play music
            r'\b(set|remind|schedule)\s+(timer|alarm)',  # set timer
            r'\b(calculate|math|compute)\b',  # calculation requests
            r'\b(weather|news|time|date)\b',  # information queries
            r'\b(shutdown|restart|exit|quit)\b',  # system commands
            r'\b(help|options|menu)\b',  # help requests
        ]

        # Define patterns for important personal information
        important_patterns = [
            (r'\b(flight|trip|travel|journey)\b.*\b(\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\b', 'event'),
            (r'\b(appointment|meeting|doctor|dentist|appointment)\b.*\b(\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\b', 'appointment'),
            (r'\b(birthday|anniversary|wedding)\b.*\b(\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\b', 'event'),
            (r'\b(address|location|home|apartment|house)\b.*\b(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|court|ct|circle|cir|boulevard|blvd|place|plz)\b', 'location'),
            (r'\b(phone|mobile|contact|number)\b.*\b(?:\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\(\d{3}\)\s*\d{3}[-.\s]?\d{4})\b', 'contact'),
            (r'\b(email|gmail|outlook|yahoo)\b.*\b[\w\.-]+@[\w\.-]+\.\w+\b', 'contact'),
            (r'\b(password|pin|code|secret|login|username)\b', 'security'),
            (r'\b(money|bank|account|credit|debit|card|payment)\b', 'finance'),
            (r'\b(medical|doctor|hospital|medication|pill|tablet)\b', 'health'),
            (r'\b(name|called|named|nickname|alias)\b.*\b\w+\b', 'identity'),
            (r'\b(age|born|birth|year|old)\b.*\b\d{4}\b', 'identity'),
            (r'\b(work|job|company|position|title|employer)\b', 'work'),
        ]

        user_input_lower = user_input.lower()

        # Check for general commands first
        for pattern in general_patterns:
            if re.search(pattern, user_input_lower):
                return 'general', 'command'

        # Check for important personal information
        for pattern, category in important_patterns:
            if re.search(pattern, user_input_lower):
                return 'important', category

        # Additional check for important info without dates
        important_without_dates = [
            r'\b(prefer|like|love|enjoy|favorite|dislike|hate)\b.*\b\w+\b',  # preferences
            r'\b(friend|family|relative|mom|dad|brother|sister|son|daughter|wife|husband|spouse|child|kid|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)\b',  # relationships
            r'\b(allergy|condition|disease|symptom|medicine|drug|treatment)\b',  # health info
            r'\b(dream|goal|plan|hope|wish|aspiration)\b',  # personal aspirations
        ]

        for pattern in important_without_dates:
            if re.search(pattern, user_input_lower):
                return 'important', 'personal_info'

        # Default classification
        return 'general', 'conversation'

    def extract_important_information(self, user_input, ai_response=""):
        """
        Extract important personal information from conversation
        """
        important_info = {}

        # Extract dates and events
        date_patterns = [
            (r'\b(flight|trip|travel|journey)\b.*?(\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\b', 'flight'),
            (r'\b(appointment|meeting|doctor|dentist)\b.*?(\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\b', 'appointment'),
            (r'\b(birthday|anniversary|wedding)\b.*?(\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2})\b', 'event'),
        ]

        for pattern, category in date_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            if matches:
                important_info[category] = matches

        # Extract contact information
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b(?:\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\(\d{3}\)\s*\d{3}[-.\s]?\d{4})\b'
        address_pattern = r'\b\d+\s+\w+(?:\s+\w+)*\s+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|court|ct|circle|cir|boulevard|blvd|place|plz)\b'

        emails = re.findall(email_pattern, user_input, re.IGNORECASE)
        phones = re.findall(phone_pattern, user_input)
        addresses = re.findall(address_pattern, user_input, re.IGNORECASE)

        if emails:
            important_info['emails'] = emails
        if phones:
            important_info['phones'] = phones
        if addresses:
            important_info['addresses'] = addresses

        # Extract preferences
        preference_pattern = r'\b(I\s+|you\s+)?(love|like|enjoy|prefer|favorite|adore|am\s+fond\s+of)\b\s+(\w+(?:\s+\w+)*)'
        preferences = re.findall(preference_pattern, user_input, re.IGNORECASE)
        if preferences:
            important_info['preferences'] = [pref[2] for pref in preferences]

        # Extract relationships - Multiple patterns to catch different sentence structures
        # Use first match to avoid overlapping matches
        relationship_patterns = [
            r'\b(this is my|meet my)\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)\s+(\w+(?:\s+\w+)*)\b',  # "this is my girlfriend Sarah"
            r'\b(my|his|her|their)\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)(?:\'s name is|\s+is)\s+(\w+(?:\s+\w+)*)',  # "my girlfriend's name is Sarah" or "my girlfriend is Sarah"
            r'\b(\w+(?:\s+\w+)*)\s+is my\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-husband)\b',  # "Sarah is my girlfriend"
            r'\b(i have|have)\s+a\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)\s+(?:named|called|is)\s+(\w+(?:\s+\w+)*)\b',  # "I have a girlfriend named Sarah"
            r'\b(her|his|their)\s+name\s+is\s+(\w+(?:\s+\w+)*)\b.*\b(girlfriend|boyfriend|gf|bf|partner|spouse|wife|husband)\b',  # "her name is Akansha, my girlfriend"
            r'\b(girlfriend|boyfriend|gf|bf|partner|spouse|wife|husband)\s+(?:is\s+)?(?:named|called|is)\s+(\w+(?:\s+\w+)*)\b',  # "girlfriend is Akansha" or "girlfriend named Akansha"
            r'\b(girlfriend|boyfriend|gf|bf|partner|spouse|wife|husband),?\s+(?:her|his|their)\s+name\s+is\s+(\w+(?:\s+\w+)*)\b',  # "girlfriend, her name is Akansha"
            r'\b(i have|have)\s+a\s+(mom|dad|mother|father|brother|sister|son|daughter|wife|husband|spouse|friend|colleague|boss|employee|girlfriend|boyfriend|gf|bf|partner|crush|date|ex|ex-girlfriend|ex-boyfriend|ex-wife|ex-husband)[^,]*,\s*i\s+love\s+(?:her|him)[^,]*,\s+(?:her|his|their)\s+name\s+is\s+(\w+(?:\s+\w+)*)\b',  # "I have a girlfriend, I love her, her name is Akansha"
        ]

        relationships = []
        # Find the first matching pattern to avoid overlapping matches
        for pattern in relationship_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            if matches:
                relationships.extend(matches)
                # For this specific use case, we only want the first set of matches to avoid duplicates
                # But we still need to check other patterns in case they match different parts of the sentence
                # Actually, let's collect all unique matches but avoid duplicates by checking if we already have a match for the same relationship type
                break  # Just take the first match to avoid overlapping

        # If no match from the first pass, try all patterns (for cases where multiple relationships are mentioned)
        if not relationships:
            for pattern in relationship_patterns:
                matches = re.findall(pattern, user_input, re.IGNORECASE)
                if matches:
                    relationships.extend(matches)

        if relationships:
            important_info['relationships'] = relationships

        return important_info

    def process_conversation_for_memory(self, user_input, ai_response):
        """
        Process conversation to determine what should be stored in long-term memory
        """
        classification, category = self.classify_conversation_content(user_input, ai_response)

        if classification == 'important':
            # Extract and store important information
            important_info = self.extract_important_information(user_input, ai_response)

            # Store in appropriate long-term memory sections
            for key, value in important_info.items():
                if key in ['flight', 'appointment', 'event']:
                    self.remember_semantic_fact('life_events', f"{key}: {value}", confidence=0.6)
                    self.remember_personal_event(key, str(value)) # Legacy sync
                elif key == 'emails':
                    self.remember_semantic_fact('contact', f"email: {value}", confidence=0.8)
                    self.remember_contact_info('email', value)
                elif key == 'phones':
                    self.remember_semantic_fact('contact', f"phone: {value}", confidence=0.8)
                    self.remember_contact_info('phone', value)
                elif key == 'preferences':
                    for pref in value:
                        self.remember_semantic_fact('preferences', f"likes {pref}", confidence=0.5)
                        self.remember_interest(pref)
                elif key == 'relationships':
                    for rel in value:
                        person = ""
                        rel_type = ""
                        if len(rel) == 3:
                            person = rel[2]
                            rel_type = rel[1]
                        elif len(rel) == 2:
                            person = rel[0] if rel[1] in ["friend", "father", "mother", "mom", "dad"] else rel[1]
                            rel_type = rel[1] if rel[1] in ["friend", "father", "mother", "mom", "dad"] else rel[0]
                        
                        if person and rel_type:
                            self.remember_semantic_fact('relationships', f"{person} is {rel_type}", confidence=0.6)
                            self.remember_relationship(person, rel_type) # Legacy sync

            print(f"Stored important information: {important_info}")
            return True

        return False  # Indicates general command, no important info to store

    def get_short_term_as_string(self, count=5):
        """Format recent conversations as a single string for LLM context"""
        recent = self.short_term[-count:]
        context_lines = []
        for entry in recent:
            if isinstance(entry, dict) and 'user' in entry:
                context_lines.append(f"User: {entry['user']}")
                context_lines.append(f"AI: {entry['ai']}")
                if 'mood' in entry:
                    context_lines.append(f"Mood: {entry['mood']}")
            else:
                # Handle legacy string entries
                context_lines.append(f"Context: {str(entry)}")
        return "\n".join(context_lines)

        # Add working memory context
        if self.working_memory:
            entities = [m['entity'] for m in self.working_memory]
            context_parts.append(f"Immediate Context (Entities): {', '.join(entities)}")

        # Add semantic facts (Verified only)
        verified_facts = []
        for subject, facts in self.semantic_memory.items():
            for f in facts:
                if f['confidence'] > 0.6 or f['confirmed']:
                    verified_facts.append(f"{subject}: {f['fact']}")
        if verified_facts:
            context_parts.append(f"Verified Facts: {', '.join(verified_facts[:15])}")

        return "\n".join(context_parts)

    def add_episodic_summary(self, summary, mood="neutral"):
        """ Summarize a session for episodic memory """
        entry = {
            'date': datetime.datetime.now().isoformat(),
            'summary': summary,
            'mood': mood,
            'importance': 1.0
        }
        self.episodic_memory.append(entry)
        self.prune_episodic_memory()
        self.save_memory()

    def prune_episodic_memory(self):
        """ Expire episodic memory older than 30 days """
        now = datetime.datetime.now()
        self.episodic_memory = [e for e in self.episodic_memory 
                               if (now - datetime.datetime.fromisoformat(e['date'])).days < 30]

    def forget_this(self, keyword):
        """ Professional 'Forget this' capability """
        keyword = keyword.lower()
        # Clear from long_term
        if keyword in self.long_term: del self.long_term[keyword]
        # Clear from semantic
        if keyword in self.semantic_memory: del self.semantic_memory[keyword]
        # Search and remove from facts/relationships
        self.relationships = {p: d for p, d in self.relationships.items() if keyword not in p.lower()}
        self.save_memory()
        return f"I have purged all records of {keyword} from my systems, Sir."

    def add_fact(self, subject, fact):
        """Add a factual memory"""
        if 'facts' not in self.long_term:
            self.long_term['facts'] = {}
        if subject not in self.long_term['facts']:
            self.long_term['facts'][subject] = []
        self.long_term['facts'][subject].append(fact)
        self.save_memory()

    def get_facts(self, subject):
        """Get facts about a subject"""
        if 'facts' in self.long_term and subject in self.long_term['facts']:
            return self.long_term['facts'][subject]
        return []

    def remember_preference(self, category, preference):
        """Remember a user preference"""
        if 'preferences' not in self.long_term:
            self.long_term['preferences'] = {}
        self.long_term['preferences'][category] = preference
        self.save_memory()

    def get_preference(self, category):
        """Get a user preference"""
        if 'preferences' in self.long_term and category in self.long_term['preferences']:
            return self.long_term['preferences'][category]
        return None

    # ===== Session Management =====

    def add_session(self, summary: str):
        """Save a session summary"""
        session = {
            'timestamp': datetime.datetime.now().isoformat(),
            'summary': summary
        }
        self.sessions.append(session)
        # Keep last 50 sessions
        if len(self.sessions) > 50:
            self.sessions.pop(0)
        self.save_memory()

    def get_recent_sessions(self, count: int = 5) -> List[Dict]:
        """Get recent session summaries"""
        return self.sessions[-count:] if self.sessions else []

    # ===== Task Memory =====

    def add_task(self, task_name: str, task_data: Dict[str, Any]):
        """Remember an ongoing task"""
        self.tasks[task_name] = {
            'created': datetime.datetime.now().isoformat(),
            'updated': datetime.datetime.now().isoformat(),
            'data': task_data
        }
        self.save_memory()

    def update_task(self, task_name: str, task_data: Dict[str, Any]):
        """Update an existing task"""
        if task_name in self.tasks:
            self.tasks[task_name]['updated'] = datetime.datetime.now().isoformat()
            self.tasks[task_name]['data'].update(task_data)
            self.save_memory()

    def get_task(self, task_name: str) -> Optional[Dict]:
        """Retrieve a task"""
        return self.tasks.get(task_name)

    def complete_task(self, task_name: str):
        """Mark a task as complete and archive it"""
        if task_name in self.tasks:
            del self.tasks[task_name]
            self.save_memory()

    def list_tasks(self) -> List[str]:
        """List all active tasks"""
        return list(self.tasks.keys())

    # ===== Semantic Search with Embeddings =====

    def _load_embeddings_model(self):
        """Lazy load the sentence transformer model"""
        if self.embeddings_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Memory: Embeddings model loaded.")
            except ImportError:
                print("Memory: sentence-transformers not installed. Semantic search disabled.")
                return False
        return True

    def _build_embeddings_cache(self):
        """Build embeddings cache from long-term memory"""
        if not self._load_embeddings_model():
            return

        self.memory_texts = []
        self.memory_embeddings = []

        # Add user preferences
        for key, value in self.long_term.items():
            text = f"{key}: {value}"
            self.memory_texts.append(text)

        # Add session summaries
        for session in self.sessions:
            self.memory_texts.append(session['summary'])

        # Add tasks
        for task_name, task_info in self.tasks.items():
            text = f"Task {task_name}: {task_info['data']}"
            self.memory_texts.append(text)

        # Add personal information
        if self.personality_profile:
            self.memory_texts.append(f"Personality: {self.personality_profile}")
        if self.interests:
            self.memory_texts.append(f"Interests: {', '.join(list(self.interests))}")
        if self.favorites:
            self.memory_texts.append(f"Favorites: {self.favorites}")
        if self.habits:
            self.memory_texts.append(f"Habits: {self.habits}")

        if self.memory_texts:
            self.memory_embeddings = self.embeddings_model.encode(self.memory_texts)
            print(f"Memory: Built embeddings cache with {len(self.memory_texts)} items.")

    def search_memory(self, query: str, top_k: int = 3) -> List[str]:
        """Search memory using semantic similarity"""
        if not self._load_embeddings_model():
            return []

        # Rebuild cache if needed
        if not self.memory_embeddings or len(self.memory_embeddings) == 0:
            self._build_embeddings_cache()

        if not self.memory_texts:
            return []

        # Encode query
        query_embedding = self.embeddings_model.encode([query])[0]

        # Calculate similarities
        similarities = np.dot(self.memory_embeddings, query_embedding)

        # Get top-k results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        results = [self.memory_texts[i] for i in top_indices]

        return results

    def get_memory_stats(self):
        """Get statistics about memory usage"""
        stats = {
            'short_term_count': len(self.short_term),
            'long_term_keys': len(self.long_term),
            'session_count': len(self.sessions),
            'task_count': len(self.tasks),
            'emotion_count': len(self.emotions),
            'interest_count': len(self.interests),
            'habit_count': len(self.habits),
            'has_facts': 'facts' in self.long_term,
            'has_preferences': 'preferences' in self.long_term,
            'personality_traits': len(self.personality_profile.get('traits', []))
        }

        if 'facts' in self.long_term:
            stats['fact_count'] = sum(len(facts) for facts in self.long_term['facts'].values())

        return stats

    def clear_short_term_memory(self):
        """Clear short-term memory"""
        self.short_term = []
        print("Short-term memory cleared.")
        self.save_memory()

    def prepare_for_exit(self):
        """
        Prepare for program exit by clearing only temporary memory
        while preserving important long-term memory.
        Generates an episodic summary of the session.
        """
        # 1. Generate episodic summary if there was conversation
        if self.short_term:
            summary = self.get_short_term_as_string(count=5)
            self.add_episodic_summary(f"Interaction highlights: {summary}", mood=self.get_current_mood())

        # 2. Clear only short-term memory and temporary context
        self.short_term = []
        self.temporary_context = []

        # 3. Save the cleaned memory state
        self.save_memory()
        print("Temporary memory cleared. Episodic summary saved. Long-term memory preserved.")

    def clear_long_term_memory(self, category=None):
        """Clear long-term memory, optionally by category"""
        if category:
            if category in self.long_term:
                del self.long_term[category]
                print(f"Long-term memory category '{category}' cleared.")
        else:
            self.long_term = {}
            print("All long-term memory cleared.")
        self.save_memory()

    def export_memory(self, filepath):
        """Export memory to a file"""
        try:
            data = {
                'long_term': self.long_term,
                'short_term': self.short_term,
                'sessions': self.sessions,
                'tasks': self.tasks,
                'emotions': self.emotions,
                'personality_profile': self.personality_profile,
                'conversation_patterns': self.conversation_patterns,
                'relationships': self.relationships,
                'habits': self.habits,
                'interests': list(self.interests),
                'favorites': self.favorites,
                'personal_history': self.personal_history
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False, default=str)
            return f"Memory exported to {filepath}"
        except Exception as e:
            return f"Failed to export memory: {e}"

    def import_memory(self, filepath):
        """Import memory from a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.long_term = data.get('long_term', {})
                self.short_term = data.get('short_term', [])
                self.sessions = data.get('sessions', [])
                self.tasks = data.get('tasks', {})
                self.emotions = data.get('emotions', [])
                self.personality_profile = data.get('personality_profile', {})
                self.conversation_patterns = data.get('conversation_patterns', {})
                self.relationships = data.get('relationships', {})
                self.habits = data.get('habits', {})
                self.interests = set(data.get('interests', []))
                self.favorites = data.get('favorites', {})
                self.personal_history = data.get('personal_history', [])
            self.save_memory()
            return f"Memory imported from {filepath}"
        except Exception as e:
            return f"Failed to import memory: {e}"