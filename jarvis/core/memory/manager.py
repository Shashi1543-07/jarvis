import os
import re
import datetime
from typing import List, Optional, Dict, Any
from .entries import MemoryEntry, MemoryType, MemorySource
from .structures import ShortTermMemory, LongTermMemory, EpisodicMemory

class MemoryManager:
    """
    Gatekeeper for all memory operations.
    Validates proposals, routes to layers, and enforces safety.
    """
    def __init__(self, config_dir=None):
        if not config_dir:
            config_dir = os.path.join(os.getcwd(), 'config')
        
        self.stm = ShortTermMemory()
        self.ltm = LongTermMemory(os.path.join(config_dir, 'memory_long_term.json'))
        self.em = EpisodicMemory(os.path.join(config_dir, 'memory_episodic.json'))
        
        # PII Regex blocklist
        self.pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b", # SSN-like
            r"\b\d{16}\b",             # CC-like
            r"\bpassword\s*[:=]\s*\S+\b" # "password = 123"
        ]

    def propose_write(self, content: str, memory_type: MemoryType, confidence: float, source=MemorySource.INFERRED_AI) -> Dict:
        """
        Main entry point for storing memory.
        Returns: {success: bool, message: str}
        """
        # 1. Validation
        if not self._validate_content(content):
            return {"success": False, "message": "Content rejected: PII or invalid format."}
            
        if confidence < 0.4:
            return {"success": False, "message": "Content rejected: Low confidence."}

        # 2. Creation
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            confidence=confidence,
            source=source
        )

        # 3. Routing
        if memory_type == MemoryType.SHORT_TERM:
            self.stm.add(entry)
            return {"success": True, "message": "Stored in Short-Term Memory"}
            
        elif memory_type == MemoryType.LONG_TERM:
            # Check for existing
            # TODO: Improve duplicate check with semantic search
            self.ltm.add(entry)
            return {"success": True, "message": f"Persisted to Long-Term Memory: {content}"}
            
        elif memory_type == MemoryType.EPISODIC:
            self.em.add_episode(content)
            return {"success": True, "message": "Episode logged."}
            
        return {"success": False, "message": "Unknown memory type"}

    def retrieve(self, query: str, include_stm=True) -> List[MemoryEntry]:
        """
        Retrieve relevant memories across layers.
        """
        results = []
        
        # LTM Search (Semantic/Keyword)
        ltm_results = self.ltm.search(query, threshold=0.3)
        results.extend(ltm_results)
        
        # STM Search (Basic scan)
        if include_stm:
            # Simplistic STM scan
            for entry in self.stm.buffer:
                if any(w in entry.content.lower() for w in query.lower().split()):
                    results.append(entry)
                    
        return results

    def _validate_content(self, content: str) -> bool:
        """Check for PII or junk"""
        if len(content) < 3: return False
        
        for pattern in self.pii_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"MemoryManager blocked PII write: {content}")
                return False
                
        return True
    
    def get_full_context(self) -> str:
        """Get STM context + High importance LTM facts"""
        return self.stm.get_context()
