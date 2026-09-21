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
            scored_results = []

            for item in self._items:
                title = item.title.lower()
                content = item.content.lower()

                score = 0

                for word in words:
                    if word in title:
                        score += 3

                    if word in content:
                        score += 1

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


# Scientific inference
knowledge.add(
    "مثال على استنتاج علمي",
    "إذا أظهرت مجموعة من التجارب أن ارتفاع درجة الحرارة ضمن "
    "نطاق محدد يرتبط بزيادة معدل تفاعل معين، فيمكن استنتاج "
    "وجود علاقة بين درجة الحرارة ومعدل التفاعل ضمن شروط التجربة. "
    "هذا الاستنتاج يعتمد على البيانات المتاحة ولا يعني بالضرورة "
    "وجود علاقة عامة في جميع الظروف.",
    "internal-scientific",
    "inference"
)
