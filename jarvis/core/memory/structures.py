import json
import os
import datetime
from collections import deque
from typing import List, Optional
from .entries import MemoryEntry, MemoryType, MemorySource

class ShortTermMemory:
    """
    In-memory ring buffer for conversation context.
    NOT persisted to disk. Cleared on restart.
    """
    def __init__(self, capacity=15):
        self.buffer = deque(maxlen=capacity)
    
    def add(self, entry: MemoryEntry):
        if entry.memory_type != MemoryType.SHORT_TERM:
            raise ValueError("ShortTermMemory only accepts SHORT_TERM entries")
        self.buffer.append(entry)
        
    def get_context(self) -> str:
        """Format as string for LLM context"""
        return "\n".join([e.content for e in self.buffer])
        
    def clear(self):
        self.buffer.clear()

class EpisodicMemory:
    """
    Daily summaries of events. Append-only log.
    """
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.entries = self._load()
        
    def _load(self) -> List[MemoryEntry]:
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [MemoryEntry.from_dict(d) for d in data]
        except Exception as e:
            print(f"Error loading Episodic Memory: {e}")
            return []
            
    def _save(self):
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
        except Exception as e:
            print(f"Error saving Episodic Memory: {e}")

    def add_episode(self, content: str, importance: float = 0.5):
        entry = MemoryEntry(
            content=content,
            memory_type=MemoryType.EPISODIC,
            confidence=1.0, # Summaries are usually trusted
            source=MemorySource.SYSTEM,
            metadata={"importance": importance}
        )
        self.entries.append(entry)
        self._save()

class LongTermMemory:
    """
    Fact and Preference storage. 
    Uses simple list + JSON persistence for now.
    TODO: Integrate Vector Search here.
    """
    def __init__(self, storage_path):
        self.storage_path = storage_path
        self.entries = self._load()
        
        # Placeholder for embeddings model
        self.embeddings_model = None
        self.vectors = None 
        
    def _load(self) -> List[MemoryEntry]:
        if not os.path.exists(self.storage_path):
            return []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [MemoryEntry.from_dict(d) for d in data]
        except Exception as e:
            print(f"Error loading LongTerm Memory: {e}")
            return []
            
    def _save(self):
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
        except Exception as e:
            print(f"Error saving LongTerm Memory: {e}")

    def add(self, entry: MemoryEntry):
        if entry.memory_type != MemoryType.LONG_TERM:
             raise ValueError("LongTermMemory only accepts LONG_TERM entries")
        
        # Deduplication check (simple exact match)
        for e in self.entries:
            if e.content == entry.content:
                # Update existing
                e.last_accessed = datetime.datetime.now().isoformat()
                e.confidence = min(1.0, e.confidence + 0.1) # Reinforce
                self._save()
                return
                
        self.entries.append(entry)
        self._save()
        
    def search(self, query: str, threshold=0.0) -> List[MemoryEntry]:
        # TODO: Implement semantic search
        # For now, keyword matching
        results = []
        query_words = query.lower().split()
        for entry in self.entries:
            score = 0
            content_lower = entry.content.lower()
            for w in query_words:
                if w in content_lower:
                    score += 1
            if score > 0:
                results.append((score, entry))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results]

    def params(self):
        return {"count": len(self.entries)}
