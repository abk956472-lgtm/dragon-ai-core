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

    def search(self, query: str):
        query = query.lower().strip()

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
            "إلى",
            "هل",
            "و",
            "أو",
            "مع",
            "هذا",
            "هذه",
            "ذلك",
            "تلك",
            "التي",
            "الذي"
        }

        words = [
            word
            for word in query.split()
            if len(word) > 2 and word not in ignored_words
        ]

        with self._lock:
            scored_results = []

            for item in self._items:
                title = item.title.lower()
                content = item.content.lower()

                score = 0
                matched_words = 0

                # مطابقة السؤال كاملًا
                if query in title:
                    score += 20

                if query in content:
                    score += 5

                # مطابقة الكلمات المهمة
                for word in words:
                    if word in title:
                        score += 10
                        matched_words += 1

                    elif word in content:
                        score += 2
                        matched_words += 1

                if matched_words > 0 or query in title:
                    scored_results.append(
                        (
                            score,
                            matched_words,
                            item
                        )
                    )

            scored_results.sort(
                key=lambda result: (
                    result[0],
                    result[1]
                ),
                reverse=True
            )

            return [
                item
                for score, matched_words, item
                in scored_results
            ]

    def clear(self):
        with self._lock:
            self._items.clear()


knowledge = KnowledgeBase()


# ==============================
# Scientific Knowledge
# ==============================

# Scientific fact
knowledge.add(
    "الخلية",
    "الخلية هي الوحدة الأساسية في بناء الكائنات الحية ووظائفها. "
    "تختلف الخلايا في بنيتها ووظائفها، وتوجد خلايا بدائية النوى "
    "وخلايا حقيقية النوى.",
    "internal-scientific",
    "fact"
)


# Scientific hypothesis
knowledge.add(
    "مث
