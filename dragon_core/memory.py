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

    def _normalize_arabic(self, text: str):
        text = text.lower().strip()

        replacements = {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ة": "ه",
            "ى": "ي",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        punctuation = "،؛؟!.,:;()[]{}\"'"

        for mark in punctuation:
            text = text.replace(mark, " ")

        return text

    def search_scientific(self, query: str):
        normalized_query = self._normalize_arabic(query)

        query_words = {
            word
            for word in normalized_query.split()
            if len(word) > 2
        }

        if not query_words:
            return []

        with self._lock:
            scored_results = []

            for item in self._items:
                if item.memory_type != "scientific":
                    continue

                normalized_content = self._normalize_arabic(
                    item.content
                )

                content_words = set(
                    normalized_content.split()
                )

                matched_words = query_words.intersection(
                    content_words
                )

                score = len(matched_words)

                if normalized_query in normalized_content:
                    score += 5

                if score > 0:
                    scored_results.append(
                        (score, item)
                    )

            scored_results.sort(
                key=lambda result: result[0],
                reverse=True
            )

            return [
                item
                for score, item in scored_results
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
