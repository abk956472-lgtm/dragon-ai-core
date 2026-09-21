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

        punctuation = "،؛؟!.,:;()[]{}\"'"

        for mark in punctuation:
            text = text.replace(mark, " ")

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
            original_word = word

            for prefix in prefixes:
                if (
                    word.startswith(prefix)
                    and len(word) > len(prefix) + 2
                ):
                    word = word[len(prefix):]
                    break

            if word.startswith("ال") and len(word) > 4:
                word = word[2:]

            if word:
                normalized_words.append(word)

        return " ".join(normalized_words)

    def search(self, query: str):
        normalized_query = self._normalize_arabic(query)

        if not normalized_query:
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
            "ماهي",
            "ماهو",
        }

        words = [
            word
            for word in normalized_query.split()
            if len(word) > 2
            and word not in ignored_words
        ]

        with self._lock:
            scored_results = []

            for item in self._items:
                title = self._normalize_arabic(item.title)
                content = self._normalize_arabic(item.content)

                score = 0
                matched_words = 0

                if normalized_query in title:
                    score += 20

                if normalized_query in content:
                    score += 5

                for word in words:
                    if word in title:
                        score += 10
                        matched_words += 1
                    elif word in content:
                        score += 2
                        matched_words += 1

                if matched_words > 0:
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
