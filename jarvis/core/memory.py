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
                    self.sessions = data.get('sessions', [])
                    self.tasks = data.get('tasks', {})
            else:
                self.long_term = {}
                self.sessions = []
                self.tasks = {}
            print("Memory: Loaded.")
        except Exception as e:
            print(f"Memory: Failed to load: {e}")
            self.long_term = {}
            self.sessions = []
            self.tasks = {}

    def save_memory(self):
        """Save all memory to persistent storage"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            data = {
                'long_term': self.long_term,
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
