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
        if knowledge_results:
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

            return response

        return (
            "لا توجد لدي حاليًا معلومات مرتبطة بهذا السؤال "
            "في قاعدة المعرفة."
        )

    def _apply_scientific_policy(
        self,
        response: str,
        knowledge_type: str
    ) -> str:

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
