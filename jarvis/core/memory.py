import json
import os
import datetime
from typing import List, Dict, Any, Optional
import numpy as np

class Memory:
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        self.memory_file = os.path.join(self.config_dir, 'memory.json')
        
        # Core memory structures
        self.long_term = {}  # Key-value storage for user preferences
        self.short_term = []  # Last 10 conversation turns
        self.sessions = []  # Session history
        self.tasks = {}  # Ongoing tasks
        
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
                    self.short_term = data.get('short_term', []) # Added short_term persistence
                    self.sessions = data.get('sessions', [])
                    self.tasks = data.get('tasks', {})
            else:
                self.long_term = {}
                self.short_term = []
                self.sessions = []
                self.tasks = {}
            print("Memory: Loaded.")
        except Exception as e:
            print(f"Memory: Failed to load: {e}")
            self.long_term = {}
            self.short_term = []
            self.sessions = []
            self.tasks = {}

    def save_memory(self):
        """Save all memory to persistent storage"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            data = {
                'long_term': self.long_term,
                'short_term': self.short_term, # Added short_term persistence
                'sessions': self.sessions,
                'tasks': self.tasks
            }
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("Memory: Saved.")
        except Exception as e:
            print(f"Memory: Failed to save: {e}")

    # ===== Basic Key-Value Storage =====
    
    def get(self, key):
        """Get a value from long-term memory"""
        return self.long_term.get(key)

    def set(self, key, value):
        """Set a value in long-term memory"""
        self.long_term[key] = value
        self.save_memory()

    def remember_context(self, text):
        """Add to short-term conversation memory"""
        self.short_term.append(text)
        if len(self.short_term) > 10:  # Keep last 10 interactions
            self.short_term.pop(0)
        self.save_memory() # Auto-save context

    def remember_conversation(self, user_input, ai_response):
        """Remember a complete conversation turn"""
        conversation_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'user': user_input,
            'ai': ai_response
        }
        self.short_term.append(conversation_entry)
        if len(self.short_term) > 10:  # Keep last 10 interactions
            self.short_term.pop(0)
        self.save_memory() # Auto-save turn

    def get_recent_conversations(self, count=5):
        """Get recent conversation entries"""
        recent = self.short_term[-count:]
        conversations = []
        for entry in recent:
            if isinstance(entry, dict) and 'user' in entry:
                conversations.append(entry)
            else:
                # Handle legacy string entries
                conversations.append({'user': 'Previous context', 'ai': str(entry)})
        return conversations

    def get_short_term_as_string(self, count=5):
        """Format recent conversations as a single string for LLM context"""
        recent = self.get_recent_conversations(count)
        context_lines = []
        for conv in recent:
            context_lines.append(f"User: {conv['user']}")
            context_lines.append(f"AI: {conv['ai']}")
        return "\n".join(context_lines)

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

    def remember_relationship(self, entity1, relation, entity2):
        """Remember relationships between entities"""
        if 'relationships' not in self.long_term:
            self.long_term['relationships'] = []
        relationship = {
            'entity1': entity1,
            'relation': relation,
            'entity2': entity2,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.long_term['relationships'].append(relationship)
        self.save_memory()

    def get_relationships(self, entity=None):
        """Get relationships, optionally filtered by entity"""
        if 'relationships' not in self.long_term:
            return []

        if entity:
            return [rel for rel in self.long_term['relationships']
                   if rel['entity1'] == entity or rel['entity2'] == entity]
        return self.long_term['relationships']

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

    def search_by_category(self, query: str, category: str, top_k: int = 3) -> List[str]:
        """Search specific category of memory using semantic similarity"""
        if not self._load_embeddings_model():
            return []

        # Build cache for specific category
        self._build_embeddings_cache_by_category(category)

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

    def _build_embeddings_cache_by_category(self, category: str):
        """Build embeddings cache for a specific category"""
        if not self._load_embeddings_model():
            return

        self.memory_texts = []
        self.memory_embeddings = []

        if category == 'facts':
            for subject, facts in self.long_term.get('facts', {}).items():
                for fact in facts:
                    text = f"{subject}: {fact}"
                    self.memory_texts.append(text)
        elif category == 'preferences':
            for pref_key, pref_value in self.long_term.get('preferences', {}).items():
                text = f"Preference for {pref_key}: {pref_value}"
                self.memory_texts.append(text)
        elif category == 'relationships':
            for rel in self.long_term.get('relationships', []):
                text = f"{rel['entity1']} {rel['relation']} {rel['entity2']}"
                self.memory_texts.append(text)
        elif category == 'conversations':
            for entry in self.short_term:
                if isinstance(entry, dict) and 'user' in entry:
                    text = f"User said: {entry['user']}. AI replied: {entry['ai']}"
                    self.memory_texts.append(text)
        elif category == 'sessions':
            for session in self.sessions:
                self.memory_texts.append(session['summary'])
        elif category == 'tasks':
            for task_name, task_info in self.tasks.items():
                text = f"Task {task_name}: {task_info['data']}"
                self.memory_texts.append(text)
        else:  # All categories
            self._build_embeddings_cache()
            return

        if self.memory_texts:
            self.memory_embeddings = self.embeddings_model.encode(self.memory_texts)
            print(f"Memory: Built {category} embeddings cache with {len(self.memory_texts)} items.")

    def get_memory_stats(self):
        """Get statistics about memory usage"""
        stats = {
            'short_term_count': len(self.short_term),
            'long_term_keys': len(self.long_term),
            'session_count': len(self.sessions),
            'task_count': len(self.tasks),
            'has_facts': 'facts' in self.long_term,
            'has_preferences': 'preferences' in self.long_term,
            'has_relationships': 'relationships' in self.long_term
        }

        if 'facts' in self.long_term:
            stats['fact_count'] = sum(len(facts) for facts in self.long_term['facts'].values())

        if 'relationships' in self.long_term:
            stats['relationship_count'] = len(self.long_term['relationships'])

        return stats

    def clear_short_term_memory(self):
        """Clear short-term memory"""
        self.short_term = []
        print("Short-term memory cleared.")
        self.save_memory()

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
                'tasks': self.tasks
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
            self.save_memory()
            return f"Memory imported from {filepath}"
        except Exception as e:
            return f"Failed to import memory: {e}"
