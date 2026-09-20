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

    def _generate_response(self, message: str, knowledge_results):
        if knowledge_results:
            return (
                "وجدت معلومات مرتبطة بطلبك في قاعدة المعرفة."
            )

        return (
            "DRAGON AI CORE استلم رسالتك بنجاح. "
            "محرك الذكاء العلمي قيد التطوير."
        )


dragon_engine = DragonEngine()
