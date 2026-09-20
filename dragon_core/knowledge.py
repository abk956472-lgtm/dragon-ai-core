from dataclasses import dataclass
from threading import Lock


@dataclass
class KnowledgeItem:
    title: str
    content: str
    source: str = "internal"


class KnowledgeBase:
    def __init__(self):
        self._items = []
        self._lock = Lock()

    def add(self, title: str, content: str, source: str = "internal"):
        item = KnowledgeItem(
            title=title,
            content=content,
            source=source
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
                if query in item.title.lower()
                or query in item.content.lower()
            ]

    def clear(self):
        with self._lock:
            self._items.clear()


knowledge = KnowledgeBase()


# Initial scientific knowledge
knowledge.add(
    "الخلية",
    "الخلية هي الوحدة الأساسية في بناء الكائنات الحية ووظائفها. "
    "تختلف الخلايا في بنيتها ووظائفها، وتوجد خلايا بدائية النوى "
    "وخلايا حقيقية النوى.",
    "internal-scientific"
)
