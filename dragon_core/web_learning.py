from .memory import memory
from .knowledge import knowledge
from .security import security
from .self_learning import self_learning
from .web_learning import web_learning

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

        if message.startswith("تعلم |"):
            return self._process_learning_command(message)

        if message.startswith("تعلم ذاتي |"):
            return self._process_self_learning_command(message)

        if message.startswith("تعلم من الويب |"):
            return self._process_web_learning_command(message)

        if message.startswith("تعلم أن "):
            return self._process_natural_learning(message)

        knowledge_results = knowledge.search(message)
        previous_memories = memory.search_scientific(message)

        # إذا لم توجد معرفة كافية، يبحث DRAGON تلقائياً في الويب
        if not knowledge_results:
            web_result = self._process_automatic_web_search(
                message,
                previous_memories
            )

            if web_result is not None:
                return web_result

        response, raw_response_for_memory, evidence_evaluation = (
            self._generate_response(
                message,
                knowledge_results,
                previous_memories
            )
        )

        if raw_response_for_memory.strip():
            memory.add(
                "assistant",
                raw_response_for_memory,
                memory_type="scientific",
                evidence_status=evidence_evaluation.get(
                    "evidence_status",
                    "unknown"
                ),
                confidence=evidence_evaluation.get(
                    "confidence",
                    "low"
                )
            )

        return {
            "status": "success",
            "response": response,
            "knowledge_matches": len(knowledge_results),
            "scientific_memory_matches": len(previous_memories),
            "scientific_policy_version": scientific_policy_version(),
            "scientific_rules_active": len(self.scientific_rules),
            "evidence_status": evidence_evaluation.get(
                "evidence_status"
            ),
            "evidence_confidence": evidence_evaluation.get(
                "confidence"
            ),
            "security_confirmation_required": (
                security.requires_confirmation()
            )
        }

    def _process_automatic_web_search(
        self,
        question: str,
        previous_memories
    ):
        result = web_learning.search_web(question)

        if not result:
            return None

        if result.get("status") != "success":
            return None

        results = result.get("results", [])

        if not results:
            return None

        saved_count = 0
        response_sections = []

        for index, item in enumerate(results, start=1):
            title = str(item.get("title", "")).strip()
            url = str(item.get("url", "")).strip()
            snippet = str(item.get("snippet", "")).strip()
            content = str(item.get("content", "")).strip()

            # نستخدم المحتوى الكامل عندما يكون متاحاً،
            # وإلا نستخدم ملخص نتيجة البحث.
            answer_text = content or snippet

            if not answer_text:
                continue

            response_sections.append(
                f"المصدر {index}:\n"
                f"{title}\n"
                f"{answer_text}\n"
                f"الرابط: {url}"
            )

            # حفظ نتائج الويب كمعرفة غير متحقق منها.
            # لا يتم تقديمها على أنها حقيقة علمية مؤكدة.
            if title and url:
                save_result = knowledge.learn(
                    title=title,
                    content=answer_text,
                    source=url,
                    knowledge_type="web_unverified"
                )

                if save_result.get("status") in (
                    "learned",
                    "duplicate"
                ):
                    saved_count += 1

        if not response_sections:
            return None

        final_response = (
            "بحثت تلقائياً في الويب لأن قاعدة المعرفة الحالية "
            "لم تحتوي على إجابة كافية.\n\n"
            + "\n\n".join(response_sections)
            + "\n\n"
            "حالة الأدلة: غير متحقق منها."
        )

        if previous_memories:
            final_response += (
                "\n\n"
                + self._build_memory_response(previous_memories)
            )

        memory.add(
            "assistant",
            final_response,
            memory_type="scientific",
            evidence_status="web_unverified",
            confidence="low"
        )

        return {
            "status": "success",
            "response": final_response,
            "knowledge_matches": 0,
            "scientific_memory_matches": len(previous_memories),
            "web_search_used": True,
            "web_results": len(response_sections),
            "knowledge_saved": saved_count,
            "evidence_status": "web_unverified",
            "evidence_confidence": "low",
            "scientific_policy_version": scientific_policy_version(),
            "scientific_rules_active": len(self.scientific_rules),
            "security_confirmation_required": (
                security.requires_confirmation()
            )
        }

    def _process_learning_command(self, message: str) -> dict:
        parts = [part.strip() for part in message.split("|")]

        if len(parts) != 5:
            return {
                "status": "error",
                "message": (
                    "صيغة التعلم غير صحيحة. استخدم: "
                    "تعلم | العنوان | المحتوى | المصدر | "
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

        return self._build_command_response(
            result,
            "manual_learning"
        )

    def _process_self_learning_command(self, message: str) -> dict:
        parts = [part.strip() for part in message.split("|")]

        if len(parts) != 5:
            return {
                "status": "error",
                "message": (
                    "صيغة التعلم الذاتي غير صحيحة. استخدم: "
                    "تعلم ذاتي | العنوان | المحتوى | المصدر | "
                    "fact/inference/hypothesis"
                )
            }

        _, title, content, source, knowledge_type = parts

        result = self_learning.learn(
            title=title,
            content=content,
            source=source,
            knowledge_type=knowledge_type
        )

        return self._build_command_response(
            result,
            "self_learning"
        )

    def _process_web_learning_command(self, message: str) -> dict:
        parts = [part.strip() for part in message.split("|")]

        if len(parts) != 4:
            return {
                "status": "error",
                "message": (
                    "صيغة التعلم من الويب غير صحيحة. استخدم: "
                    "تعلم من الويب | الرابط | العنوان | "
                    "fact/inference/hypothesis"
                )
            }

        _, url, title, knowledge_type = parts

        result = web_learning.learn_from_url(
            url=url,
            title=title,
            knowledge_type=knowledge_type,
            confidence="low"
        )

        return self._build_command_response(
            result,
            "web_learning"
        )

    def _process_natural_learning(self, message: str) -> dict:
        content = message[len("تعلم أن "):].strip()

        if not content:
            return {
                "status": "error",
                "message": "لم تحدد المعلومة التي تريد أن أتعلمها."
            }

        result = knowledge.learn(
            title="معلومة متعلمة",
            content=content,
            source="user-natural-learning",
            knowledge_type="fact"
        )

        status = result.get("status")

        responses = {
            "learned": "تم تعلم المعلومة وحفظها في قاعدة المعرفة.",
            "duplicate": (
                "هذه المعلومة موجودة بالفعل في قاعدة المعرفة."
            )
        }

        response_msg = responses.get(
            status,
            "لم يتم حفظ المعلومة."
        )

        res = self._build_command_response(
            result,
            "natural_learning"
        )

        res["response"] = response_msg

        return res

    def _build_command_response(
        self,
        result: dict,
        engine_name: str
    ) -> dict:
        return {
            "status": result.get("status", "unknown"),
            "learning_engine": engine_name,
            "learning": result,
            "scientific_policy_version": scientific_policy_version(),
            "scientific_rules_active": len(self.scientific_rules),
            "security_confirmation_required": (
                security.requires_confirmation()
            )
        }

    def _generate_response(
        self,
        message,
        knowledge_results,
        previous_memories
    ):
        if not knowledge_results:
            if previous_memories:
                mem_resp = self._build_memory_response(
                    previous_memories
                )

                eval_data = {
                    "evidence_status": "memory_based",
                    "confidence": "low"
                }

                return mem_resp, mem_resp, eval_data

            fallback_resp = (
                "لا توجد لدي حاليًا معلومات مرتبطة بهذا السؤال "
                "في قاعدة المعرفة."
            )

            eval_data = {
                "evidence_status": "insufficient",
                "confidence": "low"
            }

            return fallback_resp, fallback_resp, eval_data

        if len(knowledge_results) == 1:
            result = knowledge_results[0]

            base_response = (
                f"{result.content}\n"
                f"نوع المعرفة: {result.knowledge_type}\n"
                f"المصدر: {result.source}"
            )

            raw_response = base_response

            base_response = self._apply_scientific_policy(
                base_response,
                result.knowledge_type
            )

            evidence_evaluation = evaluate_evidence(
                facts_count=(
                    1 if result.knowledge_type == "fact" else 0
                ),
                inference_count=(
                    1
                    if result.knowledge_type == "inference"
                    else 0
                ),
                hypothesis_count=(
                    1
                    if result.knowledge_type == "hypothesis"
                    else 0
                )
            )

            final_response = base_response

            if previous_memories:
                final_response += (
                    "\n\n"
                    + self._build_memory_response(
                        previous_memories
                    )
                )

            return (
                final_response,
                raw_response,
                evidence_evaluation
            )

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

        raw_response = (
            "وجدت عدة معلومات مرتبطة بالسؤال:\n\n"
            + "\n\n".join(sections)
        )

        final_response = (
            raw_response
            + "\n\n"
            + self._build_scientific_assessment(
                evidence_evaluation
            )
        )

        if previous_memories:
            final_response += (
                "\n\n"
                + self._build_memory_response(
                    previous_memories
                )
            )

        return (
            final_response,
            raw_response,
            evidence_evaluation
        )

    def _build_memory_response(
        self,
        previous_memories
    ) -> str:
        if not previous_memories:
            return ""

        latest_memory = previous_memories[-1]

        return (
            "من الذاكرة العلمية السابقة:\n"
            f"{latest_memory.content}\n"
            "حالة الأدلة السابقة: "
            f"{latest_memory.evidence_status or 'غير محددة'}\n"
            "درجة الثقة السابقة: "
            f"{latest_memory.confidence or 'غير محددة'}"
        )

    def _build_scientific_assessment(
        self,
        evidence_evaluation
    ) -> str:
        return (
            "التقييم العلمي:\n"
            f"حالة الأدلة: "
            f"{evidence_evaluation.get('evidence_status')}\n"
            f"درجة الثقة: "
            f"{evidence_evaluation.get('confidence')}\n"
            f"التفسير: "
            f"{evidence_evaluation.get('reason')}"
        )

    def _apply_scientific_policy(
        self,
        response: str,
        knowledge_type: str
    ) -> str:
        policies = {
            "fact": (
                "الحالة العلمية: حقيقة مسجلة "
                "في قاعدة المعرفة."
            ),
            "inference": (
                "الحالة العلمية: استنتاج يعتمد على "
                "المعلومات والبيانات المتاحة، "
                "وليس حقيقة عامة بالضرورة."
            ),
            "hypothesis": (
                "الحالة العلمية: فرضية وليست حقيقة مثبتة، "
                "وتحتاج إلى أدلة وتجارب للتحقق منها."
            ),
            "web_unverified": (
                "الحالة العلمية: معلومات مسترجعة من الويب "
                "ولم يتم التحقق منها علميًا بعد."
            )
        }

        policy_note = policies.get(
            knowledge_type,
            "الحالة العلمية: نوع المعرفة غير معروف."
        )

        return f"{response}\n{policy_note}"


dragon_engine = DragonEngine()
