from dataclasses import dataclass
from datetime import datetime
from threading import Lock


@dataclass
class MemoryItem:
    role: str
    content: str
    created_at: str


class MemoryStore:
    def __init__(self):
        self._items = []
        self._lock = Lock()

    def add(self, role: str, content: str):
        item = MemoryItem(
            role=role,
            content=content,
            created_at=datetime.utcnow().isoformat()
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

    def clear(self):
        with self._lock:
            self._items.clear()


memory = MemoryStore()
