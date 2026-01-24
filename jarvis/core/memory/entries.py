from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
import datetime
import uuid

class MemoryType(Enum):
    SHORT_TERM = "short_term"   # Conversation context
    WORKING = "working_memory"  # Active task state
    LONG_TERM = "long_term"     # Facts, Preferences
    EPISODIC = "episodic"       # Summarized events

class MemorySource(Enum):
    EXPLICIT_USER = "explicit_user" # "Remember that..."
    INFERRED_AI = "inferred_ai"     # "I see you like..."
    SYSTEM = "system"               # Automated saves

@dataclass
class MemoryEntry:
    content: str
    memory_type: MemoryType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    confidence: float = 1.0
    source: MemorySource = MemorySource.EXPLICIT_USER
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "type": self.memory_type.value,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "confidence": self.confidence,
            "source": self.source.value,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            content=data.get("content"),
            memory_type=MemoryType(data.get("type")),
            created_at=data.get("created_at"),
            last_accessed=data.get("last_accessed"),
            confidence=data.get("confidence", 1.0),
            source=MemorySource(data.get("source", "explicit_user")),
            metadata=data.get("metadata", {})
        )
