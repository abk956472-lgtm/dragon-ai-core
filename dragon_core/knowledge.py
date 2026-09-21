from dataclasses import dataclass
from threading import Lock


@dataclass
class KnowledgeItem:
    title: str
    content: str
    source: str = "internal"
    knowledge_type: str = "fact"


class KnowledgeBase:
    def __init__(self):
        self._items = []
        self._lock = Lock()

    def add(
        self,
        title: str,
        content: str,
        source: str = "internal",
        knowledge_type: str = "fact"
    ):
        allowed_types = {
            "fact",
            "inference",
            "hypothesis"
        }

        if knowledge_type not in allowed_types:
            raise ValueError(
                "knowledge_type must be fact, inference, or hypothesis."
            )

        item = KnowledgeItem(
            title=title,
            content=content,
            source=source,
            knowledge_type=knowledge_type
        )

        with self._lock:
            self._items.append(item)

    def get_all(self):
        with self._lock:
            return list(self._items)

    def _normalize_arabic(self, text: str) -> str:
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

        words = text.split()
        normalized_words = []

        prefixes = (
            "وال",
            "بال",
            "كال",
            "فال",
            "لل",
            "و",
            "ف",
            "ب",
            "ك",
            "ل",
        )

        for word in words:
            for prefix in prefixes:
                if word.startswith(prefix) and len(word) > len(prefix) + 2:
                    word = word[len(prefix):]
                    break

            if word.startswith("ال") and len(word) > 4:
                word = word[2:]

            normalized_words.append(word)

        return " ".join(normalized_words)

    def search(self, query: str):
        query = self._normalize_arabic(query)

        if not query:
            return []

        ignored_words = {
            "ما",
            "ماذا",
            "هي",
            "هو",
            "من",
            "عن",
            "في",
            "على",
            "الى",
            "هل",
            "و",
            "او",
            "مع",
            "هذا",
            "هذه",
            "ذلك",
            "تلك",
            "التي",
            "الذي",
        }

        words = [
            word
            for word in query.split()
            if len(word) > 2 and word not in ignored_words
        ]

        with self._lock:
            scored_results = []

            for item in self._items:
                title = self._normalize_arabic(item.title)
                content = self._normalize_arabic(item.content)

                score = 0
                matched_words = 0

                if query in title:
                    score += 20

                if query in content:
                    score += 5

                for word in words:
                    if word in title:
                        score += 10
                        matched_words += 1

                    elif
