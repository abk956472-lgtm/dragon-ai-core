import os
import re

from dataclasses import dataclass
from threading import Lock

from supabase import create_client


# ==========================================================
# Supabase Configuration
# ==========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_SECRET_KEY:
    try:
        supabase = create_client(
            SUPABASE_URL,
            SUPABASE_SECRET_KEY
        )
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")
else:
    print("Warning: SUPABASE_URL or SUPABASE_SECRET_KEY not set. Running KnowledgeBase in in-memory mode.")


# ==========================================================
# Knowledge Item
# ==========================================================

@dataclass
class KnowledgeItem:
    title: str
    content: str
    source: str = "internal"
    knowledge_type: str = "fact"


# ==========================================================
# Knowledge Base
# ==========================================================

class KnowledgeBase:
    """
    Knowledge Engine الأساسي لـ DRAGON AI CORE.

    مسؤول عن:

    - تخزين المعرفة
    - تحميل المعرفة من Supabase
    - البحث في المعرفة
    - تصنيف المعرفة
    - منع التكرار
    - دعم المعرفة العلمية
    - دعم المعرفة المسترجعة من الويب

    مهم:

    Knowledge Engine منفصل عن Memory Engine.

    Memory:
        يتذكر معلومات مرتبطة بالمحادثات والسياق.

    Knowledge:
        يخزن معلومات يمكن استخدامها كمصدر معرفي.
    """

    # ======================================================
    # Allowed Knowledge Types
    # ======================================================

    ALLOWED_TYPES = {
        "fact",
        "inference",
        "hypothesis",
        "web_unverified"
    }

    def __init__(self):

        self._items = []
        self._lock = Lock()

        self._load_from_database()

    # ======================================================
    # Load From Database
    # ======================================================

    def _load_from_database(self):

        if not supabase:
            return

        try:

            response = (
                supabase
                .table("knowledge")
                .select(
                    "title,content,source,knowledge_type"
                )
                .execute()
            )

            rows = response.data or []

        except Exception:
            rows = []

        with self._lock:

            self._items = [
                KnowledgeItem(
                    title=row.get(
                        "title",
                        ""
                    ),
                    content=row.get(
                        "content",
                        ""
                    ),
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
                if row.get("content")
            ]

    # ======================================================
    # Validate Knowledge Type
    # ======================================================

    def _validate_knowledge_type(
        self,
        knowledge_type: str
    ):

        return (
            knowledge_type
            in self.ALLOWED_TYPES
        )

    # ======================================================
    # Add
    # ======================================================

    def add(
        self,
        title: str,
        content: str,
        source: str = "internal",
        knowledge_type: str = "fact"
    ):

        title = str(
            title or ""
        ).strip()

        content = str(
            content or ""
        ).strip()

        source = str(
            source or "internal"
        ).strip()

        knowledge_type = str(
            knowledge_type or "fact"
        ).strip().lower()

        if not title:
            raise ValueError(
                "Knowledge title is required."
            )

        if not content:
            raise ValueError(
                "Knowledge content is required."
            )

        if not self._validate_knowledge_type(
            knowledge_type
        ):
            raise ValueError(
                "knowledge_type must be "
                "fact, inference, hypothesis, "
                "or web_unverified."
            )

        item = KnowledgeItem(
            title=title,
            content=content,
            source=source,
            knowledge_type=knowledge_type
        )

        # ----------------------------------------------
        # Duplicate Check
        # ----------------------------------------------

        with self._lock:

            for existing in self._items:

                if (
                    existing.title == title
                    and existing.content == content
                    and existing.source == source
                    and existing.knowledge_type
                    == knowledge_type
                ):
                    return existing

        # ----------------------------------------------
        # Database
        # ----------------------------------------------

        if supabase:
            try:

                supabase.table(
                    "knowledge"
                ).insert(
                    {
                        "title": title,
                        "content": content,
                        "source": source,
                        "knowledge_type": knowledge_type
                    }
                ).execute()

            except Exception as error:

                raise RuntimeError(
                    f"Database error: {error}"
                )

        # ----------------------------------------------
        # Local Cache
        # ----------------------------------------------

        with self._lock:
            self._items.append(item)

        return item

    # ==========================================================
    # Learn
    # ==========================================================

    def learn(
        self,
        title: str,
        content: str,
        source: str,
        knowledge_type: str
    ) -> dict:

        title = str(
            title or ""
        ).strip()

        content = str(
            content or ""
        ).strip()

        source = str(
            source or ""
        ).strip()

        knowledge_type = str(
            knowledge_type or ""
        ).strip().lower()

        # ----------------------------------------------
        # Validation
        # ----------------------------------------------

        if not title:

            return {
                "status": "rejected",
                "reason": (
                    "Knowledge title is required."
                )
            }

        if not content:

            return {
                "status": "rejected",
                "reason": (
                    "Knowledge content is required."
                )
            }

        if not source:

            return {
                "status": "rejected",
                "reason": (
                    "Knowledge source is required."
                )
            }

        if not self._validate_knowledge_type(
            knowledge_type
        ):

            return {
                "status": "rejected",
                "reason": (
                    "knowledge_type must be "
                    "fact, inference, hypothesis, "
                    "or web_unverified."
                )
            }

        # ----------------------------------------------
        # Duplicate Check
        # ----------------------------------------------

        with self._lock:

            for item in self._items:

                if (
                    item.title == title
                    and item.content == content
                    and item.source == source
                    and item.knowledge_type
                    == knowledge_type
                ):

                    return {
                        "status": "duplicate",
                        "reason": (
                            "This knowledge already exists."
                        )
                    }

        # ----------------------------------------------
        # Save To Supabase
        # ----------------------------------------------

        if supabase:
            try:

                supabase.table(
                    "knowledge"
                ).insert(
                    {
                        "title": title,
                        "content": content,
                        "source": source,
                        "knowledge_type":
                            knowledge_type
                    }
                ).execute()

            except Exception as error:

                return {
                    "status": "error",
                    "reason": (
                        f"Database error: {error}"
                    )
                }

        # ----------------------------------------------
        # Add To Local Cache
        # ----------------------------------------------

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
            "knowledge_type":
                knowledge_type,
            "source": source
        }

    # ==========================================================
    # Get All
    # ==========================================================

    def get_all(self):

        with self._lock:
            return list(
                self._items
            )

    # ==========================================================
    # Arabic Normalization
    # ==========================================================

    def _normalize_arabic(
        self,
        text: str
    ) -> str:

        text = str(
            text or ""
        ).lower().strip()

        replacements = {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ة": "ه",
            "ى": "ي",
        }

        for old, new in replacements.items():

            text = text.replace(
                old,
                new
            )

        punctuation = (
            "،؛؟!.,:;()[]{}\"'`"
            "«»“”‘’"
        )

        for mark in punctuation:

            text = text.replace(
                mark,
                " "
            )

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
                    and len(word)
                    > len(prefix) + 2
                ):

                    word = word[
                        len(prefix):
                    ]

                    break

            if (
                word.startswith("ال")
                and len(word) > 4
            ):

                word = word[2:]

            if word:

                normalized_words.append(
                    word
                )

        return " ".join(
            normalized_words
        )

    # ==========================================================
    # Tokenizer
    # ==========================================================

    def _tokenize(
        self,
        text: str
    ):

        normalized = (
            self._normalize_arabic(
                text
            )
        )

        return set(
            re.findall(
                r"[a-z0-9\u0600-\u06ff]+",
                normalized
            )
        )

    # ==========================================================
    # Search
    # ==========================================================

    def search(
        self,
        query: str
    ):

        normalized_query = (
            self._normalize_arabic(
                query
            )
        )

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

        query_tokens = self._tokenize(
            normalized_query
        )

        words = {
            word
            for word in query_tokens
            if (
                len(word) > 2
                and word not in ignored_words
            )
        }

        if not words:
            return []

        with self._lock:

            scored_results = []

            for item in self._items:

                title_tokens = (
                    self._tokenize(
                        item.title
                    )
                )

                content_tokens = (
                    self._tokenize(
                        item.content
                    )
                )

                title_matches = (
                    words.intersection(
                        title_tokens
                    )
                )

                content_matches = (
                    words.intersection(
                        content_tokens
                    )
                )

                matched_words = (
                    title_matches
                    | content_matches
                )

                if not matched_words:
                    continue

                score = 0

                # ------------------------------------------
                # Exact title phrase
                # ------------------------------------------

                if (
                    normalized_query
                    in self._normalize_arabic(
                        item.title
                    )
                ):

                    score += 50

                # ------------------------------------------
                # Exact content phrase
                # ------------------------------------------

                if (
                    normalized_query
                    in self._normalize_arabic(
                        item.content
                    )
                ):

                    score += 15

                # ------------------------------------------
                # Title Matches
                # ------------------------------------------

                score += (
                    len(title_matches)
                    * 10
                )

                # ------------------------------------------
                # Content Matches
                # ------------------------------------------

                score += (
                    len(content_matches)
                    * 2
                )

                total_query_words = len(
                    words
                )

                matched_count = len(
                    matched_words
                )

                # ------------------------------------------
                # Minimum relevance
                # ------------------------------------------

                if total_query_words >= 2:

                    if matched_count < 2:
                        continue

                if (
                    not title_matches
                    and len(content_matches) < 2
                ):

                    continue

                # ------------------------------------------
                # Knowledge Type Adjustment
                # ------------------------------------------

                if item.knowledge_type == "fact":

                    score += 3

                elif item.knowledge_type == "inference":

                    score += 1

                elif item.knowledge_type == "hypothesis":

                    score += 0

                elif (
                    item.knowledge_type
                    == "web_unverified"
                ):

                    score -= 2

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
                for score,
                matched_words,
                item
                in scored_results
            ]

    # ==========================================================
    # Search By Knowledge Type
    # ==========================================================

    def search_by_type(
        self,
        knowledge_type: str
    ):

        knowledge_type = str(
            knowledge_type or ""
        ).strip().lower()

        with self._lock:

            return [
                item
                for item in self._items
                if (
                    item.knowledge_type
                    == knowledge_type
                )
            ]

    # ==========================================================
    # Search Scientific Knowledge
    # ==========================================================

    def search_scientific(
        self,
        query: str
    ):

        results = self.search(
            query
        )

        scientific_sources = {
            "internal-scientific",
            "scientific",
            "research",
        }

        return [
            item
            for item in results
            if (
                item.source
                in scientific_sources
                or item.knowledge_type
                in {
                    "fact",
                    "inference",
                    "hypothesis"
                }
            )
        ]

    # ==========================================================
    # Clear Local Cache
    # ==========================================================

    def clear(self):

        with self._lock:
            self._items.clear()


# ==========================================================
# Global Knowledge Engine
# ==========================================================

knowledge = KnowledgeBase()


# ==========================================================
# Initial Scientific Knowledge
# ==========================================================

def _ensure_initial_knowledge():

    initial_items = [

        (
            "الخلية",

            "الخلية هي الوحدة الأساسية في بناء "
            "الكائنات الحية ووظائفها. "
            "تختلف الخلايا في بنيتها ووظائفها، "
            "وتوجد خلايا بدائية النوى "
            "وخلايا حقيقية النوى.",

            "internal-scientific",

            "fact"
        ),

        (
            "مثال على فرضية علمية",

            "هذه فرضية علمية توضيحية وليست "
            "حقيقة مثبتة: قد يؤثر عامل بيئي "
            "معين في معدل نمو كائن حي، "
            "لكن إثبات هذه الفرضية يتطلب "
            "تجارب وبيانات قابلة للتحقق.",

            "internal-scientific",

            "hypothesis"
        ),

        (
            "مثال على استنتاج علمي",

            "إذا أظهرت مجموعة من التجارب أن "
            "ارتفاع درجة الحرارة ضمن نطاق "
            "محدد يرتبط بزيادة معدل تفاعل معين، "
            "فيمكن استنتاج وجود علاقة بين "
            "درجة الحرارة ومعدل التفاعل ضمن "
            "شروط التجربة. "
            "هذا الاستنتاج يعتمد على البيانات "
            "المتاحة ولا يعني بالضرورة وجود "
            "علاقة عامة في جميع الظروف.",

            "internal-scientific",

            "inference"
        )
    ]

    for (
        title,
        content,
        source,
        knowledge_type
    ) in initial_items:

        try:

            knowledge.add(
                title=title,
                content=content,
                source=source,
                knowledge_type=knowledge_type
            )

        except Exception:
            # إذا كانت المعلومة موجودة
            # أو قاعدة البيانات غير متاحة
            # لا نوقف استيراد النظام بالكامل.
            pass


_ensure_initial_knowledge()
