"""
DRAGON AI CORE
Self Learning Engine

محرك التعلّم الذاتي:
- يستقبل المعرفة الجديدة.
- يتحقق من سلامة المدخلات.
- يصنف المعرفة.
- يميز بين الحقيقة والاستنتاج والفرضية.
- يمنع تمرير المعرفة غير الصالحة إلى قاعدة المعرفة.
- يستخدم KnowledgeBase لحفظ المعرفة.
- يحتفظ بسجل محلي لعمليات التعلم أثناء تشغيل العملية.
- يجهز واجهة واضحة لإضافة مصادر خارجية مستقبلًا.
"""

from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional

from .knowledge import knowledge


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


class SelfLearningEngine:
    """
    المحرك المركزي للتعلّم الذاتي.

    ملاحظة:
    هذا المحرك لا يعتبر أي معلومة خارجية حقيقة تلقائيًا.
    المصدر ونوع المعرفة وحالة الأدلة تبقى منفصلة.
    """

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

    def __init__(self):
        self._records: List[LearningRecord] = []
        self._lock = Lock()

    # ==========================================================
    # Public API
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
    # Candidate creation
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
                "reason": (
                    "Invalid evidence_status."
                ),
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
    # Learning records
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
    # Knowledge inspection
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
    # Candidate preparation
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

        هذه الخطوة مهمة مستقبلًا عند استقبال
        المعلومات من الإنترنت أو مصادر خارجية.
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
    # External source interface
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

        حاليًا لا يقوم هذا الأسلوب بجلب الإنترنت بنفسه.
        بل يستقبل محتوى مصدر تم جمعه بالفعل.

        لاحقًا يمكن ربطه بموصلات مصادر موثوقة
        دون تغيير واجهة التعلم الأساسية.
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
    # Learning statistics
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
# Global self-learning engine
# ==============================================================

self_learning = SelfLearningEngine()
