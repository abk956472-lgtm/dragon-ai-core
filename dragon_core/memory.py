from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Optional, Any


@dataclass
class MemoryItem:
    role: str
    content: str
    created_at: str

    # نوع الذاكرة داخل DRAGON
    memory_type: str = "conversation"

    # نوع المعرفة العلمية إن وجد
    knowledge_type: Optional[str] = None

    # حالة الأدلة
    evidence_status: Optional[str] = None

    # درجة الثقة
    confidence: Optional[str] = None

    # مصدر الذاكرة
    source: Optional[str] = None

    # نطاق الذاكرة:
    # short_term / long_term / semantic / episodic
    memory_scope: str = "short_term"

    # أهمية الذاكرة
    importance: float = 0.5

    # بيانات إضافية قابلة للتوسع
    metadata: dict = field(default_factory=dict)


class MemoryStore:
    """
    Memory Engine الأساسي لـ DRAGON AI CORE.

    مسؤول عن:

    - تخزين الذاكرة
    - استرجاع الذاكرة
    - البحث النصي
    - البحث العلمي
    - البحث المرتبط بالسؤال
    - ترتيب الذكريات
    - منع التكرار
    - دعم Short-Term / Long-Term / Semantic / Episodic
    - تجهيز البنية لطبقة Embedding / Vector Memory مستقبلًا

    ملاحظة:

    هذا المستوى لا يعتمد مباشرة على:
    Supabase
    Ollama
    Gemini
    Claude
    أو أي مزود خارجي.

    الهدف هو إبقاء Memory Engine مستقلًا.
    """

    def __init__(self):
        self._items = []
        self._lock = Lock()

    # ==========================================================
    # Add Memory
    # ==========================================================

    def add(
        self,
        role: str,
        content: str,
        memory_type: str = "conversation",
        knowledge_type: Optional[str] = None,
        evidence_status: Optional[str] = None,
        confidence: Optional[str] = None,
        source: Optional[str] = None,
        memory_scope: str = "short_term",
        importance: float = 0.5,
        metadata: Optional[dict] = None
    ):
        """
        إضافة ذاكرة جديدة.

        حافظنا على جميع الوسائط القديمة حتى لا تنكسر
        الملفات الموجودة في DRAGON.
        """

        content = str(content or "").strip()

        if not content:
            return None

        # حماية قيمة importance
        try:
            importance = float(importance)
        except (TypeError, ValueError):
            importance = 0.5

        importance = max(
            0.0,
            min(1.0, importance)
        )

        item = MemoryItem(
            role=role,
            content=content,
            created_at=datetime.utcnow().isoformat(),
            memory_type=memory_type,
            knowledge_type=knowledge_type,
            evidence_status=evidence_status,
            confidence=confidence,
            source=source,
            memory_scope=memory_scope,
            importance=importance,
            metadata=metadata or {}
        )

        with self._lock:

            # منع تكرار الذاكرة نفسها
            normalized_new = self._normalize_arabic(
                content
            )

            for existing in self._items:

                normalized_existing = (
                    self._normalize_arabic(
                        existing.content
                    )
                )

                if (
                    normalized_new
                    and normalized_new == normalized_existing
                    and existing.role == role
                    and existing.memory_type == memory_type
                ):
                    return existing

            self._items.append(item)

        return item

    # ==========================================================
    # Get All
    # ==========================================================

    def get_all(self):
        with self._lock:
            return list(self._items)

    # ==========================================================
    # Basic Search
    # ==========================================================

    def search(self, query: str):

        query = str(
            query or ""
        ).lower().strip()

        if not query:
            return []

        with self._lock:

            return [
                item
                for item in self._items
                if query in item.content.lower()
            ]

    # ==========================================================
    # Arabic Normalization
    # ==========================================================

    def _normalize_arabic(
        self,
        text: str
    ):
        """
        تطبيع النص العربي قبل البحث.

        يساعد على التعامل مع اختلاف:
        أ / إ / آ
        ة / ه
        ى / ي
        """

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
            "،؛؟!.,:;()[]{}\"'«»"
        )

        for mark in punctuation:
            text = text.replace(
                mark,
                " "
            )

        return " ".join(
            text.split()
        )

    # ==========================================================
    # Token Extraction
    # ==========================================================

    def _extract_words(
        self,
        text: str
    ):
        normalized = self._normalize_arabic(
            text
        )

        return {
            word
            for word in normalized.split()
            if len(word) > 2
        }

    # ==========================================================
    # Scientific Memory Search
    # ==========================================================

    def search_scientific(
        self,
        query: str
    ):
        """
        البحث داخل الذاكرة العلمية فقط.

        هذه الوظيفة موجودة أصلًا في DRAGON
        وتم الحفاظ عليها وتطوير ترتيب النتائج.
        """

        query_words = self._extract_words(
            query
        )

        if not query_words:
            return []

        normalized_query = (
            self._normalize_arabic(
                query
            )
        )

        with self._lock:

            scored_results = []

            for item in self._items:

                if item.memory_type != "scientific":
                    continue

                normalized_content = (
                    self._normalize_arabic(
                        item.content
                    )
                )

                content_words = set(
                    normalized_content.split()
                )

                matched_words = (
                    query_words.intersection(
                        content_words
                    )
                )

                score = len(
                    matched_words
                )

                # تطابق العبارة كاملة
                if (
                    normalized_query
                    and normalized_query
                    in normalized_content
                ):
                    score += 5

                # أهمية الذاكرة
                score += item.importance

                if score > 0:

                    scored_results.append(
                        (
                            score,
                            item
                        )
                    )

            scored_results.sort(
                key=lambda result: result[0],
                reverse=True
            )

            return [
                item
                for score, item
                in scored_results
            ]

    # ==========================================================
    # Relevant Memory Search
    # ==========================================================

    def search_relevant(
        self,
        query: str,
        limit: int = 5
    ):
        """
        استرجاع الذكريات الأكثر ارتباطًا بالسؤال.

        هذه هي الطبقة التي جهزناها لكي يستطيع
        DragonEngine استخدام Memory Engine الجديد.

        حاليًا تستخدم:
        - تطبيع النص
        - تطابق الكلمات
        - تطابق العبارة
        - أهمية الذاكرة
        - نوع الذاكرة
        - حداثة الذاكرة

        وهي مصممة بحيث يمكن استبدال أو إضافة
        Vector / Embedding Search لاحقًا بدون
        تغيير DragonEngine.
        """

        query = str(
            query or ""
        ).strip()

        if not query:
            return []

        query_words = self._extract_words(
            query
        )

        if not query_words:
            return []

        normalized_query = (
            self._normalize_arabic(
                query
            )
        )

        now = datetime.utcnow()

        with self._lock:

            scored_results = []

            for item in self._items:

                normalized_content = (
                    self._normalize_arabic(
                        item.content
                    )
                )

                content_words = set(
                    normalized_content.split()
                )

                if not content_words:
                    continue

                matched_words = (
                    query_words.intersection(
                        content_words
                    )
                )

                if not matched_words:
                    continue

                # ----------------------------------------------
                # Keyword score
                # ----------------------------------------------

                keyword_score = (
                    len(matched_words)
                    / max(
                        len(query_words),
                        1
                    )
                )

                # ----------------------------------------------
                # Exact phrase score
                # ----------------------------------------------

                phrase_score = 0.0

                if (
                    normalized_query
                    and normalized_query
                    in normalized_content
                ):
                    phrase_score = 1.0

                # ----------------------------------------------
                # Importance score
                # ----------------------------------------------

                importance_score = (
                    item.importance
                )

                # ----------------------------------------------
                # Recency score
                # ----------------------------------------------

                recency_score = (
                    self._calculate_recency_score(
                        item.created_at,
                        now
                    )
                )

                # ----------------------------------------------
                # Memory type score
                # ----------------------------------------------

                type_score = 0.0

                if item.memory_type == "scientific":
                    type_score = 0.15

                elif item.memory_scope == "long_term":
                    type_score = 0.20

                elif item.memory_scope == "semantic":
                    type_score = 0.20

                elif item.memory_scope == "episodic":
                    type_score = 0.10

                # ----------------------------------------------
                # Final relevance score
                # ----------------------------------------------

                score = (
                    keyword_score * 0.50
                    + phrase_score * 0.20
                    + importance_score * 0.15
                    + recency_score * 0.10
                    + type_score * 0.05
                )

                scored_results.append(
                    (
                        score,
                        item
                    )
                )

            scored_results.sort(
                key=lambda result: result[0],
                reverse=True
            )

            return [
                item
                for score, item
                in scored_results[:limit]
            ]

    # ==========================================================
    # Recency
    # ==========================================================

    def _calculate_recency_score(
        self,
        created_at: str,
        now: datetime
    ):
        """
        يعطي الذكريات الحديثة وزنًا أعلى.

        لا يحذف الذكريات القديمة.
        """

        try:

            created = datetime.fromisoformat(
                created_at
            )

            age_days = (
                now - created
            ).total_seconds() / 86400

            if age_days <= 1:
                return 1.0

            if age_days <= 7:
                return 0.8

            if age_days <= 30:
                return 0.6

            if age_days <= 90:
                return 0.4

            return 0.2

        except Exception:
            return 0.5

    # ==========================================================
    # Scientific Memories
    # ==========================================================

    def get_scientific_memories(
        self
    ):
        with self._lock:

            return [
                item
                for item in self._items
                if item.memory_type == "scientific"
            ]

    # ==========================================================
    # Memory By Scope
    # ==========================================================

    def get_by_scope(
        self,
        memory_scope: str
    ):
        """
        استرجاع الذاكرة حسب نطاقها.

        مثل:
        short_term
        long_term
        semantic
        episodic
        """

        with self._lock:

            return [
                item
                for item in self._items
                if item.memory_scope == memory_scope
            ]

    # ==========================================================
    # Memory By Type
    # ==========================================================

    def get_by_type(
        self,
        memory_type: str
    ):

        with self._lock:

            return [
                item
                for item in self._items
                if item.memory_type == memory_type
            ]

    # ==========================================================
    # Recent Memories
    # ==========================================================

    def get_recent(
        self,
        limit: int = 10
    ):
        """
        آخر الذكريات المضافة.
        """

        with self._lock:

            return list(
                reversed(
                    self._items[-limit:]
                )
            )

    # ==========================================================
    # Memory Update
    # ==========================================================

    def update(
        self,
        item: MemoryItem,
        **updates: Any
    ):
        """
        تحديث ذاكرة موجودة.

        تمهيد لـ:
        Memory Update
        Memory Consolidation
        Conflict Handling
        """

        with self._lock:

            if item not in self._items:
                return None

            for field_name, value in updates.items():

                if hasattr(
                    item,
                    field_name
                ):
                    setattr(
                        item,
                        field_name,
                        value
                    )

            return item

    # ==========================================================
    # Memory Count
    # ==========================================================

    def count(self):
        with self._lock:
            return len(
                self._items
            )

    # ==========================================================
    # Clear
    # ==========================================================

    def clear(self):
        with self._lock:
            self._items.clear()


memory = MemoryStore()
