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
        words = query.split()

        with self._lock:
            return [
                item
                for item in self._items
                if any(
                    word in item.title.lower()
                    or word in item.content.lower()
                    for word in words
                )
            ]

    def clear(self):
        with self._lock:
            self._items.clear()


knowledge = KnowledgeBase()


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
    "مثال على فرضية علمية",
    "هذه فرضية علمية توضيحية وليست حقيقة مثبتة: "
    "قد يؤثر عامل بيئي معين في معدل نمو كائن حي، "
    "لكن إثبات هذه الفرضية يتطلب تجارب وبيانات قابلة للتحقق.",
    "internal-scientific",
    "hypothesis"
)
