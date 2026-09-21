from .memory import memory
from .knowledge import knowledge
from .security import security
from .self_learning import self_learning

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

        memory.add(
            "user",
            message
        )

        # ==============================================
        # Manual Learning Command
        #
        # تعلم | title | content | source | type
        # ==============================================

        if message.startswith("تعلم |"):
            return self._process_learning_command(message)

        # ==============================================
        # Self Learning Command
        #
        # تعلم ذاتي | title | content | source | type
        # ==============================================

        if message.startswith("تعلم ذاتي |"):
            return self._process_self_learning_command(
                message
            )

        knowledge_results = knowledge.search(message)

        previous_memories = memory.search_scientific(message)

        response, evidence_evaluation = self._generate_response(
            message,
            knowledge_results,
            previous_memories
        )

        memory_content = response

        if previous_memories:
            memory_marker = "\n\nمن الذاكرة العلمية السابقة:"

            if memory_marker in memory_content:
                memory_content = memory_content.split(
                    memory_marker,
                    1
                )[0]

        if memory_content.strip():
            memory.add(
                "assistant",
                memory_content,
                memory_type="scientific",
                evidence_status=evidence_evaluation[
                    "evidence_status"
                ],
                confidence=evidence_evaluation[
                    "confidence"
                ]
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

    # ==========================================================
    # Manual Learning
    # ==========================================================

    def _process_learning_command(
        self,
        message: str
    ) -> dict:
        parts = [
            part.strip()
            for part in message.split("|")
        ]

        if len(parts) != 5:
            return {
                "status": "error",
                "message": (
                    "صيغة التعلم غير صحيحة. "
                    "استخدم: تعلم | العنوان | المحتوى | المصدر | "
                    "fact/inference/hypothesis"
                )
            }

        _, title, content, source, knowledge_type = parts

        result = knowledge.learn(
            title=title,
            content=content,
            source=source,
            knowledge_type=knowledge_type
        )

        return {
            "status": result["status"],
            "learning": result,
            "scientific_policy_version":
                scientific_policy_version(),
            "scientific_rules_active":
                len(self.scientific_rules),
            "security_confirmation_required":
                security.requires_confirmation()
        }

    # ==========================================================
    # Self Learning
    # ==========================================================

    def _process_self_learning_command(
        self,
        message: str
    ) -> dict:
        parts = [
            part.strip()
            for part in message.split("|")
        ]

        if len(parts) != 5:
            return {
                "status": "error",
                "message": (
                    "صيغة التعلم الذ
