from .memory import memory
from .knowledge import knowledge
from .security import security
from policies.scientific_policy import (
    get_scientific_rules,
    evaluate_evidence,
    scientific_policy_version,
)


class DragonEngine:
    def __init__(self):
        self.name = "DRAGON AI CORE"
        self.scientific_rules = get_scientific_rules()

    def process(self, message: str) -> dict:
        message = message.strip()

        if not message:
            return {
                "status": "error",
                "message": "Empty message."
            }

        memory.add("user", message)

        knowledge_results = knowledge.search(message)

        previous_memories = memory.search_scientific(message)

        response, evidence_evaluation = self._generate_response(
            message,
            knowledge_results,
            previous_memories
        )

        memory.add(
            "assistant",
            response,
            memory_type="scientific",
            evidence_status=evidence_evaluation["evidence_status"],
            confidence=evidence_evaluation["confidence"]
        )

        return {
            "status": "success",
            "response": response,
            "knowledge_matches": len(knowledge_results),
            "scientific_memory_matches": len(previous_memories),
            "scientific_policy_version":
                scientific_policy_version(),
            "scientific_rules_active":
                len(self.scientific_rules),
            "evidence_status":
                evidence_evaluation["evidence_status"],
            "evidence_confidence":
                evidence_evaluation["confidence"],
            "security_confirmation_required":
                security.requires_confirmation()
        }

    def _generate_response(
        self,
        message,
        knowledge_results,
        previous_memories
    ):
        if not knowledge_results:
            if previous_memories:
                return (
                    self._build_memory_response(
                        previous_memories
                    ),
                    {
                        "evidence_status": "memory_based",
                        "confidence": "low"
                    }
                )

            return (
                "لا توجد لدي حاليًا معلومات مرتبطة بهذا السؤال "
                "في قاعدة المعرفة."
            ), {
                "evidence_status": "insufficient",
                "confidence": "low"
            }

        if len(knowledge_results) == 1:
            result = knowledge_results[0]

            response = (
                f"{result.content}\n"
                f"نوع المعرفة: {result.knowledge_type}\n"
                f"المصدر: {result.source}"
            )

            response = self._apply_scientific_policy(
                response,
                result.knowledge_type
            )

            evidence_evaluation = evaluate_evidence(
                facts_count=1
                if result.knowledge_type == "fact"
                else 0,
                inference_count=1
                if result.knowledge_type == "inference"
                else 0,
                hypothesis_count=1
                if result.knowledge_type == "hypothesis"
                else 0
            )

            if previous_memories:
                response += (
                    "\n\n"
                    + self._build_memory_response(
                        previous_memories
                    )
                )

            return response, evidence_evaluation

        sections = []

        facts_count = 0
        inference_count = 0
        hypothesis_count = 0

        for index, result in enumerate(
            knowledge_results,
            start=1
        ):
            if result.knowledge_type == "fact":
                facts_count += 1

            elif result.knowledge_type == "inference":
                inference_count += 1

            elif result.knowledge_type == "hypothesis":
                hypothesis_count += 1

            sections.append(
                f"المعلومة {index}:\n"
                f"{result.content}\n"
                f"نوع المعرفة: {result.knowledge_type}\n"
                f"المصدر: {result.source}"
            )

        evidence_evaluation = evaluate_evidence(
            facts_count=facts_count,
            inference_count=inference_count,
            hypothesis_count=hypothesis_count
        )

        response = (
            "وجدت عدة معلومات مرتبطة بالسؤال:\n\n"
            + "\n\n".join(sections)
            + "\n\n"
            + self._build_scientific_assessment(
                evidence_evaluation
            )
        )

        if previous_memories:
            response += (
                "\n\n"
                + self._build_memory_response(
                    previous_memories
                )
            )

        return response, evidence_evaluation

    def _build_memory_response(
        self,
        previous_memories
    ):
        latest_memory = previous_memories[-1]

        return (
            "من الذاكرة العلمية السابقة:\n"
            f"{latest_memory.content}\n"
            f"حالة الأدلة السابقة: "
            f"{latest_memory.evidence_status or 'غير محددة'}\n"
            f"درجة الثقة السابقة: "
            f"{latest_memory.confidence or 'غير محددة'}"
        )

    def _build_scientific_assessment(
        self,
        evidence_evaluation
    ):
        return (
            "التقييم العلمي:\n"
            f"حالة الأدلة: "
            f"{evidence_evaluation['evidence_status']}\n"
            f"درجة الثقة: "
            f"{evidence_evaluation['confidence']}\n"
            f"التفسير: "
            f"{evidence_evaluation['reason']}"
        )

    def _apply_scientific_policy(
        self,
        response: str,
        knowledge_type: str
    ):
        if knowledge_type == "fact":
            policy_note = (
                "الحالة العلمية: حقيقة مسجلة في قاعدة المعرفة."
            )

        elif knowledge_type == "inference":
            policy_note = (
                "الحالة العلمية: استنتاج يعتمد على المعلومات "
                "والبيانات المتاحة، وليس حقيقة عامة بالضرورة."
            )

        elif knowledge_type == "hypothesis":
            policy_note = (
                "الحالة العلمية: فرضية وليست حقيقة مثبتة، "
                "وتحتاج إلى أدلة وتجارب للتحقق منها."
            )

        else:
            policy_note = (
                "الحالة العلمية: نوع المعرفة غير معروف."
            )

        return f"{response}\n{policy_note}"


dragon_engine = DragonEngine()
