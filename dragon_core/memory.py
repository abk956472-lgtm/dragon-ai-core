from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Optional


@dataclass
class MemoryItem:
    role: str
    content: str
    created_at: str
    memory_type: str = "conversation"
    knowledge_type: Optional[str] = None
    evidence_status: Optional[str] = None
    confidence: Optional[str] = None


class MemoryStore:
    def __init__(self):
        self._items = []
        self._lock = Lock()

    def add(
        self,
        role: str,
        content: str,
        memory_type: str = "conversation",
        knowledge_type: Optional[str] = None,
        evidence_status: Optional[str] = None,
        confidence: Optional[str] = None
    ):
        item = MemoryItem(
            role=role,
            content=content,
            created_at=datetime.utcnow().isoformat(),
            memory_type=memory_type,
            knowledge_type=knowledge_type,
            evidence_status=evidence_status,
            confidence=confidence
        )

        with self._lock:
            self._items.append(item)

    def get_all(self):
        with self._lock:
            return list(self._items)

    def search(self, query: str):
        query = query.lower().strip()

        with self._lock:
            return [
                item
                for item in self._items
                if query in item.content.lower()
            ]

    def search_scientific(self, query: str):
        query = query.lower().strip()

        with self._lock:
            return [
                item
                for item in self._items
                if item.memory_type == "scientific"
                and query in item.content.lower()
            ]

    def get_scientific_memories(self):
        with self._lock:
            return [
                item
                for item in self._items
                if item.memory_type == "scientific"
            ]

    def clear(self):
        with self._lock:
            self._items.clear()


memory = MemoryStore()
