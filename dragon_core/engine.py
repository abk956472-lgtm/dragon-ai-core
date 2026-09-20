from .memory import memory
from .knowledge import knowledge
from .security import security


class DragonEngine:
    def __init__(self):
        self.name = "DRAGON AI CORE"

    def process(self, message: str) -> dict:
        message = message.strip()

        if not message:
            return {
                "status": "error",
                "message": "Empty message."
            }

        # Store the user's message in short-term memory.
        memory.add("user", message)

        # Search the internal knowledge base.
        knowledge_results = knowledge.search(message)

        response = self._generate_response(
            message,
            knowledge_results
        )

        # Store DRAGON's response in memory.
        memory.add("assistant", response)

        return {
            "status": "success",
            "response": response,
            "knowledge_matches": len(knowledge_results),
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
            "محرك الذكاء الأساسي قيد التطوير."
        )


dragon_engine = DragonEngine()
