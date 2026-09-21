import os
import re

from dataclasses import dataclass
from threading import Lock

from supabase import create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is not configured.")

if not SUPABASE_SECRET_KEY:
    raise RuntimeError("SUPABASE_SECRET_KEY is not configured.")


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


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

        self._load_from_database()

    def _load_from_database(self):
        response = (
            supabase
            .table("knowledge")
            .select(
                "title,content,source,knowledge_type"
            )
            .execute()
        )

        rows = response.data or []

        with self._lock:
            self._items = [
                KnowledgeItem(
                    title=row["title"],
                    content=row["content"],
                    source=row.get(
                        "source",
                        "internal"
                    ),
                    knowledge_type=row.get(
                        "knowledge_type",
                        "fact"
                    )
                )
                for row in rows
            ]

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
            for existing in self._items:
                if (
                    existing.title == title
                    and existing.content == content
                    and existing.source == source
                    and existing.knowledge_type == knowledge_type
                ):
                    return

        supabase.table("knowledge").insert({
            "title": title,
            "content": content,
            "source": source,
            "knowledge_type": knowledge_type
        }).execute()

        with self._lock:
            self._items.append(item)

    def learn(
        self,
        title: str,
        content: str,
        source: str,
        knowledge_type: str
    ) -> dict:

        title = title.strip()
        content = content.strip()
        source = source.strip()
        knowledge_type = knowledge_type.strip().lower()

        if not title:
            return {
                "status": "rejected",
                "reason": "Knowledge title is required."
            }

        if not content:
            return {
                "status": "rejected",
                "reason": "Knowledge content is required."
            }

        if not source:
            return {
                "status": "rejected",
                "reason": "Knowledge source is required."
            }

        allowed_types = {
            "fact",
            "inference",
            "hypothesis"
        }

        if knowledge_type not in allowed_types:
            return {
                "status": "rejected",
                "reason": (
                    "knowledge_type must be fact, "
                    "inference, or hypothesis."
                )
            }

        with self._lock:
            for item in self._items:
                if (
                    item.title == title
                    and item.content == content
                    and item.source == source
                    and item.knowledge_type == knowledge_type
                ):
                    return {
                        "status": "duplicate",
                        "reason": "This knowledge already exists."
                    }

        try:
            supabase.table("knowledge").insert({
                "title": title,
                "content": content,
                "source": source,
                "knowledge_type": knowledge_type
            }).execute()

        except Exception as error:
            return {
                "status": "error",
                "reason": f"Database error: {error}"
            }

        item = KnowledgeItem(
            title=title,
            content=content,
            source=source,
            knowledge_type=knowledge_type
        )

        with self._lock:
            self._items.append(item)

        return {
            "status": "learned",
            "title": title,
            "knowledge_type": knowledge_type,
            "source": source
        }

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

        punctuation = (
            "،؛؟!.,:;()[]{}\"'`"
            "«»“”‘’"
        )

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

    def _tokenize(self, text: str):
        normalized = self._normalize_arabic(text)

        return set(
            re.findall(
                r"[a-z0-9\u0600-\u06ff]+",
                normalized
            )
        )

    def search(self, query: str):
        normalized_query = self._normalize_arabic(query)

        if not normalized_query:
            return []

        ignored_words = {
            # Arabic
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

            # English
            "the",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
            "how",
            "is",
            "are",
            "was",
            "were",
            "do",
            "does",
            "did",
            "a",
            "an",
            "and",
            "or",
            "of",
            "to",
            "in",
            "on",
            "for",
            "with",
            "about",
            "from",
            "by",
            "latest",
            "current",
        }

        query_tokens = self._tokenize(normalized_query)

        words = {
            word
            for word in query_tokens
            if len(word) > 2
            and word not in ignored_words
        }

        if not words:
            return []

        with self._lock:
            scored_results = []

            for item in self._items:
                title_tokens = self._tokenize(
                    item.title
                )

                content_tokens = self._tokenize(
                    item.content
                )

                title_matches = (
                    words.intersection(title_tokens)
                )

                content_matches = (
                    words.intersection(content_tokens)
                )

                matched_words = (
                    title_matches
                    | content_matches
                )

                if not matched_words:
                    continue

                score = 0

                # تطابق كامل للعبارة في العنوان
                if normalized_query in self._normalize_arabic(
                    item.title
                ):
                    score += 50

                # تطابق كامل للعبارة في المحتوى
                if normalized_query in self._normalize_arabic(
                    item.content
                ):
                    score += 15

                # كلمات موجودة في العنوان
                score += len(title_matches) * 10

                # كلمات موجودة في المحتوى
                score += len(content_matches) * 2

                total_query_words = len(words)
                matched_count = len(matched_words)

                # لا نعتبر نتيجة ضعيفة مرتبطة بالسؤال
                if total_query_words >= 2:
                    if matched_count < 2:
                        continue

                # إذا كانت النتيجة تعتمد على المحتوى فقط
                # يجب أن يكون هناك تطابق كافٍ
                if (
                    not title_matches
                    and len(content_matches) < 2
                ):
                    continue

                scored_results.append(
                    (
                        score,
                        matched_count,
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

knowledge.add(
    "الخلية",
    "الخلية هي الوحدة الأساسية في بناء الكائنات الحية ووظائفها. "
    "تختلف الخلايا في بنيتها ووظائفها، وتوجد خلايا بدائية النوى "
    "وخلايا حقيقية النوى.",
    "internal-scientific",
    "fact"
)


knowledge.add(
    "مثال على فرضية علمية",
    "هذه فرضية علمية توضيحية وليست حقيقة مثبتة: "
    "قد يؤثر عامل بيئي معين في معدل نمو كائن حي، "
    "لكن إثبات هذه الفرضية يتطلب تجارب وبيانات قابلة للتحقق.",
    "internal-scientific",
    "hypothesis"
)


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
