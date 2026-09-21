from .memory import memory
from .knowledge import knowledge
from .security import security
from policies.scientific_policy import get_scientific_rules


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

        response = self._generate_response(
            message,
            knowledge_results
        )

        memory.add("assistant", response)

        return {
            "status": "success",
            "response": response,
            "knowledge_matches": len(knowledge_results),
            "scientific_policy_version": "1.0.0",
            "scientific_rules_active": len(self.scientific_rules),
            "security_confirmation_required":
                security.requires_confirmation()
        }

    def _generate_response(self, message, knowledge_results):
        if not knowledge_results:
            return (
                "لا توجد لدي حاليًا معلومات مرتبطة بهذا السؤال "
                "في قاعدة المعرفة."
            )

        if len(knowledge_results) == 1:
            result = knowledge_results[0]

            response = (
                f"{result.content}\n"
                f"نوع المعرفة: {result.knowledge_type}\n"
                f"المصدر: {result.source}"
            )

            return self._apply_scientific_policy(
                response,
                result.knowledge_type
            )

        sections = []

        for index, result in enumerate(
            knowledge_results,
            start=1
        ):
            sections.append(
                f"المعلومة {index}:\n"
                f"{result.content}\n"
                f"نوع المعرفة: {result.knowledge_type}\n"
                f"المصدر: {result.source}"
            )

        evidence = "\n\n".join(sections)

        inference = self._build_scientific_inference(
            knowledge_results
        )

        return (
            "وجدت عدة معلومات مرتبطة بالسؤال:\n\n"
            f"{evidence}\n\n"
            f"{inference}"
        )

    def _build_scientific_inference(
        self,
        knowledge_results
    ):
        facts = [
            item
            for item in knowledge_results
            if item.knowledge_type == "fact"
        ]

        inferences = [
            item
            for item in knowledge_results
            if item.knowledge_type == "inference"
        ]

        hypotheses = [
            item
            for item in knowledge_results
            if item.knowledge_type == "hypothesis"
        ]

        parts = []

        if facts:
            parts.append(
                "المعلومات المؤكدة المتاحة: "
                f"{len(facts)} عنصر/عناصر."
            )

        if inferences:
            parts.append(
                "الاستنتاجات الموجودة مسبقًا: "
                f"{len(inferences)} عنصر/عناصر."
            )

        if hypotheses:
            parts.append(
                "الفرضيات الموجودة: "
                f"{len(hypotheses)} عنصر/عناصر."
            )

        parts.append(
            "الاستنتاج العلمي الحالي: "
            "المعلومات المسترجعة لا تكفي وحدها لإثبات "
            "علاقة علمية جديدة بين هذه العناصر. "
            "لذلك لا يتم تحويلها إلى حقيقة دون أدلة إضافية."
        )

        return "\n".join(parts)

    def _apply_scientific_policy(
        self,
