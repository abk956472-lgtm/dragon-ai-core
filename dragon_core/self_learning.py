"""
DRAGON AI CORE
Self Learning Engine

محرك التعلّم الذاتي:

الوظائف الحالية:
- استقبال المعرفة الجديدة.
- التحقق من سلامة المدخلات.
- تصنيف المعرفة.
- التمييز بين الحقيقة والاستنتاج والفرضية.
- منع تمرير المعرفة غير الصالحة إلى قاعدة المعرفة.
- استخدام KnowledgeBase لحفظ المعرفة.
- الاحتفاظ بسجل محلي لعمليات التعلم أثناء التشغيل.

الوظائف الجديدة:
- تعريف هدف تعلم عام ومستمر.
- إنشاء خطة تعلم قابلة للتوسع.
- تتبع المجال والموضوع الحالي.
- الانتقال بين موضوعات التعلم.
- تسجيل حالة خطة التعلم.
- تجهيز واجهة مستقبلية للبحث الذاتي في الإنترنت.

ملاحظة:
هذا الملف لا يبحث في الإنترنت بنفسه حتى الآن.
البحث سيُربط لاحقًا بمحرك Web Learning.
"""


from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional


from .knowledge import knowledge


# ==============================================================
# Learning Data Models
# ==============================================================


@dataclass
class LearningCandidate:
    """
    معلومة مرشحة للتعلم قبل حفظها في قاعدة المعرفة.
    """

    title: str
    content: str
    source: str
    knowledge_type: str = "fact"
    evidence_status: str = "unverified"
    confidence: str = "low"


@dataclass
class LearningRecord:
    """
    سجل عملية تعلم واحدة.
    """

    title: str
    source: str
    knowledge_type: str
    status: str
    evidence_status: str
    confidence: str
    created_at: str


@dataclass
class LearningTopic:
    """
    موضوع واحد داخل خطة التعلم.
    """

    topic: str
    field: str
    status: str = "pending"
    priority: int = 0
    notes: str = ""


# ==============================================================
# Self Learning Engine
# ==============================================================


class SelfLearningEngine:
    """
    المحرك المركزي للتعلّم الذاتي.

    المحرك مسؤول عن:
    - استقبال المعرفة.
    - التحقق منها قبل الحفظ.
    - تسجيل عمليات التعلم.
    - إدارة خطة التعلم المستمر.

    لا يعتبر أي محتوى خارجي حقيقة مؤكدة تلقائيًا.
    """

    # ==========================================================
    # Knowledge Rules
    # ==========================================================

    ALLOWED_TYPES = {
        "fact",
        "inference",
        "hypothesis",
    }

    ALLOWED_EVIDENCE_STATUS = {
        "verified",
        "supported",
        "unverified",
        "insufficient",
        "disputed",
    }

    ALLOWED_CONFIDENCE = {
        "high",
        "moderate",
        "low",
    }

    # ==========================================================
    # Default Self Learning Goal
    # ==========================================================

    DEFAULT_LEARNING_GOAL = (
        "التعلّم المستمر واكتساب المعرفة "
        "من مصادر موثوقة ومسموح بها، "
        "مع حفظ المصدر وتمييز حالة الأدلة."
    )

    # ==========================================================
    # Initial Learning Roadmap
    # ==========================================================

    DEFAULT_LEARNING_PLAN = [
        LearningTopic(
            topic="أساسيات الذكاء الاصطناعي",
            field="الذكاء الاصطناعي",
            priority=1,
        ),
        LearningTopic(
            topic="التعلم الآلي",
            field="الذكاء الاصطناعي",
            priority=2,
        ),
        LearningTopic(
            topic="الشبكات العصبية",
            field="الذكاء الاصطناعي",
            priority=3,
        ),
        LearningTopic(
            topic="التعلم العميق",
            field="الذكاء الاصطناعي",
            priority=4,
        ),
        LearningTopic(
            topic="النماذج اللغوية الكبيرة",
            field="الذكاء الاصطناعي",
            priority=5,
        ),
        LearningTopic(
            topic="الذكاء الاصطناعي التوليدي",
            field="الذكاء الاصطناعي",
            priority=6,
        ),
        LearningTopic(
            topic="وكلاء الذكاء الاصطناعي",
            field="الذكاء الاصطناعي",
            priority=7,
        ),
    ]

    # ==========================================================
    # Initialization
    # ==========================================================

    def __init__(self):
        self._records: List[LearningRecord] = []

        self._learning_plan: List[LearningTopic] = []

        self._learning_goal = self.DEFAULT_LEARNING_GOAL

        self._current_field: Optional[str] = None

        self._current_topic: Optional[str] = None

        self._lock = Lock()

        self._initialize_learning_plan()

    # ==========================================================
    # Learning Plan Initialization
    # ==========================================================

    def _initialize_learning_plan(self):
        """
        إنشاء نسخة مستقلة من خطة التعلم الافتراضية.
        """

        with self._lock:
            self._learning_plan = [
                LearningTopic(
                    topic=item.topic,
                    field=item.field,
                    status=item.status,
                    priority=item.priority,
                    notes=item.notes,
                )
                for item in self.DEFAULT_LEARNING_PLAN
            ]

    # ==========================================================
    # Public Learning API
    # ==========================================================

    def learn(
        self,
        title: str,
        content: str,
        source: str,
        knowledge_type: str = "fact",
        evidence_status: str = "unverified",
        confidence: str = "low",
    ) -> dict:
        """
        استقبال معلومة ومحاولة تعلمها.

        لا يتم الحفظ إلا بعد اجتياز التحقق الأساسي.
        """

        candidate = self._build_candidate(
            title=title,
            content=content,
            source=source,
            knowledge_type=knowledge_type,
            evidence_status=evidence_status,
            confidence=confidence,
        )

        validation = self._validate_candidate(candidate)

        if not validation["valid"]:
            return self._record_result(
                candidate=candidate,
                status="rejected",
                reason=validation["reason"],
            )

        result = knowledge.learn(
            title=candidate.title,
            content=candidate.content,
            source=candidate.source,
            knowledge_type=candidate.knowledge_type,
        )

        status = result.get("status", "unknown")

        if status == "learned":
            return self._record_result(
                candidate=candidate,
                status="learned",
                learning=result,
            )

        if status == "duplicate":
            return self._record_result(
                candidate=candidate,
                status="duplicate",
                learning=result,
            )

        if status == "rejected":
            return self._record_result(
                candidate=candidate,
                status="rejected",
                learning=result,
            )

        if status == "error":
            return self._record_result(
                candidate=candidate,
                status="error",
                learning=result,
            )

        return self._record_result(
            candidate=candidate,
            status="unknown",
            learning=result,
        )

    # ==========================================================
    # Candidate Creation
    # ==========================================================

    def _build_candidate(
        self,
        title: str,
        content: str,
        source: str,
        knowledge_type: str,
        evidence_status: str,
        confidence: str,
    ) -> LearningCandidate:
        """
        تنظيف المدخلات وبناء مرشح معرفة.
        """

        clean_title = self._clean_text(title)
        clean_content = self._clean_text(content)
        clean_source = self._clean_text(source)

        clean_type = self._normalize_knowledge_type(
            knowledge_type
        )

        clean_evidence = self._normalize_evidence_status(
            evidence_status
        )

        clean_confidence = self._normalize_confidence(
            confidence
        )

        return LearningCandidate(
            title=clean_title,
            content=clean_content,
            source=clean_source,
            knowledge_type=clean_type,
            evidence_status=clean_evidence,
            confidence=clean_confidence,
        )

    # ==========================================================
    # Validation
    # ==========================================================

    def _validate_candidate(
        self,
        candidate: LearningCandidate,
    ) -> dict:
        """
        التحقق الأساسي من المعلومة قبل حفظها.
        """

        if not candidate.title:
            return {
                "valid": False,
                "reason": "Knowledge title is required.",
            }

        if not candidate.content:
            return {
                "valid": False,
                "reason": "Knowledge content is required.",
            }

        if not candidate.source:
            return {
                "valid": False,
                "reason": "Knowledge source is required.",
            }

        if candidate.knowledge_type not in self.ALLOWED_TYPES:
            return {
                "valid": False,
                "reason": (
                    "knowledge_type must be fact, "
                    "inference, or hypothesis."
                ),
            }

        if (
            candidate.evidence_status
            not in self.ALLOWED_EVIDENCE_STATUS
        ):
            return {
                "valid": False,
                "reason": "Invalid evidence_status.",
            }

        if candidate.confidence not in self.ALLOWED_CONFIDENCE:
            return {
                "valid": False,
                "reason": (
                    "confidence must be high, "
                    "moderate, or low."
                ),
            }

        return {
            "valid": True,
            "reason": None,
        }

    # ==========================================================
    # Normalization
    # ==========================================================

    def _clean_text(self, value: Any) -> str:
        """
        تحويل القيمة إلى نص وتنظيف المسافات.
        """

        if value is None:
            return ""

        return str(value).strip()

    def _normalize_knowledge_type(
        self,
        knowledge_type: Any,
    ) -> str:
        """
        توحيد نوع المعرفة.
        """

        if knowledge_type is None:
            return "fact"

        return str(
            knowledge_type
        ).strip().lower()

    def _normalize_evidence_status(
        self,
        evidence_status: Any,
    ) -> str:
        """
        توحيد حالة الأدلة.
        """

        if evidence_status is None:
            return "unverified"

        return str(
            evidence_status
        ).strip().lower()

    def _normalize_confidence(
        self,
        confidence: Any,
    ) -> str:
        """
        توحيد مستوى الثقة.
        """

        if confidence is None:
            return "low"

        return str(
            confidence
        ).strip().lower()

    # ==========================================================
    # Learning Records
    # ==========================================================

    def _record_result(
        self,
        candidate: LearningCandidate,
        status: str,
        reason: Optional[str] = None,
        learning: Optional[dict] = None,
    ) -> dict:
        """
        تسجيل نتيجة عملية التعلم وإرجاع نتيجة موحدة.
        """

        record = LearningRecord(
            title=candidate.title,
            source=candidate.source,
            knowledge_type=candidate.knowledge_type,
            status=status,
            evidence_status=candidate.evidence_status,
            confidence=candidate.confidence,
            created_at=datetime.utcnow().isoformat(),
        )

        with self._lock:
            self._records.append(record)

        response = {
            "status": status,
            "title": candidate.title,
            "knowledge_type": candidate.knowledge_type,
            "source": candidate.source,
            "evidence_status": candidate.evidence_status,
            "confidence": candidate.confidence,
        }

        if reason is not None:
            response["reason"] = reason

        if learning is not None:
            response["learning"] = learning

        return response

    def get_learning_records(self) -> List[LearningRecord]:
        """
        الحصول على سجل عمليات التعلم الحالية.
        """

        with self._lock:
            return list(self._records)

    def clear_learning_records(self):
        """
        مسح سجل العمليات المحلي.

        لا يحذف أي معرفة من Supabase.
        """

        with self._lock:
            self._records.clear()

    # ==========================================================
    # Knowledge Inspection
    # ==========================================================

    def get_knowledge(self) -> list:
        """
        الحصول على المعرفة الموجودة حاليًا.
        """

        return knowledge.get_all()

    def search_knowledge(
        self,
        query: str,
    ) -> list:
        """
        البحث في قاعدة المعرفة قبل أو بعد التعلم.
        """

        if not query:
            return []

        return knowledge.search(query)

    # ==========================================================
    # Candidate Preparation
    # ==========================================================

    def prepare_candidate(
        self,
        title: str,
        content: str,
        source: str,
        knowledge_type: str = "fact",
        evidence_status: str = "unverified",
        confidence: str = "low",
    ) -> dict:
        """
        تجهيز معلومة للتعلم دون حفظها.
        """

        candidate = self._build_candidate(
            title=title,
            content=content,
            source=source,
            knowledge_type=knowledge_type,
            evidence_status=evidence_status,
            confidence=confidence,
        )

        validation = self._validate_candidate(
            candidate
        )

        return {
            "valid": validation["valid"],
            "reason": validation["reason"],
            "candidate": {
                "title": candidate.title,
                "content": candidate.content,
                "source": candidate.source,
                "knowledge_type": candidate.knowledge_type,
                "evidence_status": candidate.evidence_status,
                "confidence": candidate.confidence,
            },
        }

    # ==========================================================
    # External Source Interface
    # ==========================================================

    def learn_from_source(
        self,
        title: str,
        content: str,
        source: str,
        knowledge_type: str = "fact",
        evidence_status: str = "unverified",
        confidence: str = "low",
    ) -> dict:
        """
        نقطة دخول للمصادر الخارجية.

        يستقبل محتوى مصدر تم جمعه بالفعل.
        """

        return self.learn(
            title=title,
            content=content,
            source=source,
            knowledge_type=knowledge_type,
            evidence_status=evidence_status,
            confidence=confidence,
        )

    # ==========================================================
    # Self Learning Goal
    # ==========================================================

    def get_learning_goal(self) -> str:
        """
        الحصول على الهدف العام للتعلم الذاتي.
        """

        with self._lock:
            return self._learning_goal

    def set_learning_goal(
        self,
        goal: str,
    ) -> dict:
        """
        تغيير الهدف العام للتعلم الذاتي.
        """

        clean_goal = self._clean_text(goal)

        if not clean_goal:
            return {
                "status": "rejected",
                "reason": "Learning goal is required.",
            }

        with self._lock:
            self._learning_goal = clean_goal

        return {
            "status": "updated",
            "learning_goal": clean_goal,
        }

    # ==========================================================
    # Learning Plan
    # ==========================================================

    def get_learning_plan(self) -> List[LearningTopic]:
        """
        الحصول على خطة التعلم الحالية.
        """

        with self._lock:
            return list(self._learning_plan)

    def add_learning_topic(
        self,
        topic: str,
        field: str,
        priority: int = 0,
        notes: str = "",
    ) -> dict:
        """
        إضافة موضوع جديد إلى خطة التعلم.
        """

        clean_topic = self._clean_text(topic)
        clean_field = self._clean_text(field)
        clean_notes = self._clean_text(notes)

        if not clean_topic:
            return {
                "status": "rejected",
                "reason": "Learning topic is required.",
            }

        if not clean_field:
            return {
                "status": "rejected",
                "reason": "Learning field is required.",
            }

        try:
            clean_priority = int(priority)
        except (TypeError, ValueError):
            clean_priority = 0

        with self._lock:
            for item in self._learning_plan:
                if (
                    item.topic == clean_topic
                    and item.field == clean_field
                ):
                    return {
                        "status": "duplicate",
                        "reason": "Learning topic already exists.",
                    }

            item = LearningTopic(
                topic=clean_topic,
                field=clean_field,
                priority=clean_priority,
                notes=clean_notes,
            )

            self._learning_plan.append(item)

        return {
            "status": "added",
            "topic": clean_topic,
            "field": clean_field,
            "priority": clean_priority,
        }

    # ==========================================================
    # Current Learning Topic
    # ==========================================================

    def get_current_learning_topic(self) -> Optional[dict]:
        """
        الحصول على الموضوع الحالي الذي يجب أن يتعلمه DRAGON.
        """

        with self._lock:
            for item in sorted(
                self._learning_plan,
                key=lambda topic: topic.priority
            ):
                if item.status == "pending":
                    return {
                        "topic": item.topic,
                        "field": item.field,
                        "status": item.status,
                        "priority": item.priority,
                        "notes": item.notes,
                    }

        return None

    def start_next_learning_topic(self) -> dict:
        """
        اختيار أول موضوع لم يبدأ بعد.
        """

        with self._lock:
            pending_topics = [
                item
                for item in self._learning_plan
                if item.status == "pending"
            ]

            if not pending_topics:
                return {
                    "status": "completed",
                    "message": "No pending learning topics.",
                }

            pending_topics.sort(
                key=lambda item: item.priority
            )

            selected = pending_topics[0]

            selected.status = "learning"

            self._current_field = selected.field
            self._current_topic = selected.topic

            return {
                "status": "started",
                "topic": selected.topic,
                "field": selected.field,
                "priority": selected.priority,
            }

    def complete_current_learning_topic(
        self,
        notes: str = "",
    ) -> dict:
        """
        إنهاء الموضوع الحالي.
        """

        clean_notes = self._clean_text(notes)

        with self._lock:
            if not self._current_topic:
                return {
                    "status": "error",
                    "reason": "No active learning topic.",
                }

            for item in self._learning_plan:
                if item.topic == self._current_topic:
                    item.status = "completed"

                    if clean_notes:
                        item.notes = clean_notes

                    completed_topic = item.topic

                    self._current_topic = None
                    self._current_field = None

                    return {
                        "status": "completed",
                        "topic": completed_topic,
                        "notes": item.notes,
                    }

        return {
            "status": "error",
            "reason": "Current learning topic was not found.",
        }

    # ==========================================================
    # Learning Progress
    # ==========================================================

    def learning_progress(self) -> dict:
        """
        حساب تقدم خطة التعلم.
        """

        with self._lock:
            total = len(self._learning_plan)

            pending = sum(
                1
                for item in self._learning_plan
                if item.status == "pending"
            )

            learning = sum(
                1
                for item in self._learning_plan
                if item.status == "learning"
            )

            completed = sum(
                1
                for item in self._learning_plan
                if item.status == "completed"
            )

            if total == 0:
                percentage = 0.0
            else:
                percentage = (
                    completed / total
                ) * 100

            return {
                "learning_goal": self._learning_goal,
                "total_topics": total,
                "pending": pending,
                "learning": learning,
                "completed": completed,
                "progress_percent": round(
                    percentage,
                    2,
                ),
                "current_field": self._current_field,
                "current_topic": self._current_topic,
            }

    # ==========================================================
    # Self Learning Decision Interface
    # ==========================================================

    def next_learning_action(self) -> dict:
        """
        تحديد الخطوة التالية في دورة التعلم.

        هذه الواجهة لا تبحث في الإنترنت بعد.
        هي فقط تحدد ما ينبغي فعله لاحقًا.
        """

        current = self.get_current_learning_topic()

        if current:
            return {
                "action": "learn_current_topic",
                "topic": current["topic"],
                "field": current["field"],
                "reason": (
                    "يوجد موضوع تعلم نشط يحتاج إلى "
                    "مصادر ومعرفة."
                ),
            }

        next_topic = self.get_current_learning_topic()

        if next_topic:
            return {
                "action": "start_next_topic",
                "topic": next_topic["topic"],
                "field": next_topic["field"],
                "reason": (
                    "لا يوجد موضوع نشط، ويوجد موضوع "
                    "جديد في خطة التعلم."
                ),
            }

        return {
            "action": "learning_plan_completed",
            "reason": (
                "تم الانتهاء من جميع موضوعات خطة "
                "التعلم الحالية."
            ),
        }

    # ==========================================================
    # Learning Statistics
    # ==========================================================

    def statistics(self) -> Dict[str, Any]:
        """
        إحصائيات عمليات التعلم الحالية.
        """

        with self._lock:
            records = list(self._records)

        statistics = {
            "total_learning_attempts": len(records),
            "learned": 0,
            "duplicate": 0,
            "rejected": 0,
            "error": 0,
            "unknown": 0,
            "facts": 0,
            "inferences": 0,
            "hypotheses": 0,
        }

        for record in records:
            if record.status in statistics:
                statistics[record.status] += 1

            if record.knowledge_type == "fact":
                statistics["facts"] += 1

            elif record.knowledge_type == "inference":
                statistics["inferences"] += 1

            elif record.knowledge_type == "hypothesis":
                statistics["hypotheses"] += 1

        return statistics


# ==============================================================
# Global Self Learning Engine
# ==============================================================


self_learning = SelfLearningEngine()
