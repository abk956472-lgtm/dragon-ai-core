import os
import requests

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


GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.6-flash:generateContent"
)

GEMINI_TIMEOUT = 30


class DragonEngine:
    """
    المحرك المركزي لـ DRAGON AI CORE.

    مسؤول عن:
    - استقبال الرسائل
    - التعلم اليدوي
    - التعلم الذاتي
    - التعلم من الويب
    - البحث التلقائي في الويب
    - معالجة نتائج الويب بواسطة Gemini
    - البحث في المعرفة
    - استرجاع الذاكرة العلمية
    - تطبيق السياسة العلمية
    - بناء إجابات منظمة
    """

    def __init__(self):
        self.name = "DRAGON AI CORE"
        self.scientific_rules = get_scientific_rules()

    # ==========================================================
    # Main Processing
    # ==========================================================

    def process(self, message: str) -> dict:
        message = message.strip()

        if not message:
            return {
                "status": "error",
                "message": "Empty message."
            }

        # حفظ رسالة المستخدم
        memory.add(
            "user",
            message
        )

        # ======================================================
        # Manual Learning
        # ======================================================

        if message.startswith("تعلم |"):
            return self._process_learning_command(message)

        # ======================================================
        # Self Learning
        # ======================================================

        if message.startswith("تعلم ذاتي |"):
            return self._process_self_learning_command(message)

        # ======================================================
        # Web Learning
        # ======================================================

        if message.startswith("تعلم من الويب |"):
            return self._process_web_learning_command(message)

        # ======================================================
        # Natural Learning
        # ======================================================

        if message.startswith("تعلم أن "):
            return self._process_natural_learning(message)

        # ======================================================
        # Knowledge Retrieval
        # ======================================================

        knowledge_results = knowledge.search(message)

        # ======================================================
        # Scientific Memory
        # ======================================================

        previous_memories = memory.search_scientific(message)

        # ======================================================
        # Automatic Web Search
        # ======================================================

        # إذا لم توجد معرفة داخلية كافية،
        # يبحث DRAGON تلقائيًا في الويب.
        if not knowledge_results:

            web_result = self._process_automatic_web_search(
                message,
                previous_memories
            )

            if web_result is not None:
                return web_result

        # ======================================================
        # Response Generation
        # ======================================================

        response, evidence_evaluation = self._generate_response(
            message,
            knowledge_results,
            previous_memories
        )

        # ======================================================
        # Store Assistant Memory
        # ======================================================

        memory_content = response

        # لا نخزن قسم الذاكرة داخل الذاكرة مرة أخرى.
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
    # Automatic Web Search
    # ==========================================================

    def _process_automatic_web_search(
        self,
        question: str,
        previous_memories
    ):
        """
        يبحث تلقائيًا في الويب عندما لا توجد معرفة داخلية كافية.

        المسار:

        السؤال
        -> Web Search
        -> استخراج المصادر
        -> معالجة النتائج بواسطة Gemini
        -> بناء إجابة بلغة المستخدم
        -> حفظ المصادر في قاعدة المعرفة
        -> حفظ الرد في الذاكرة العلمية
        """

        result = web_learning.search_web(
            question
        )

        if not result:
            return None

        if result.get("status") != "success":
            return None

        results = result.get(
            "results",
            []
        )

        if not results:
            return None

        saved_count = 0
        source_items = []

        for index, item in enumerate(
            results,
            start=1
        ):

            title = str(
                item.get(
                    "title",
                    ""
                )
            ).strip()

            url = str(
                item.get(
                    "url",
                    ""
                )
            ).strip()

            snippet = str(
                item.get(
                    "snippet",
                    ""
                )
            ).strip()

            content = str(
                item.get(
                    "content",
                    ""
                )
            ).strip()

            # نفضل محتوى الصفحة على نتيجة البحث المختصرة.
            answer_text = content or snippet

            if not answer_text:
                continue

            source_items.append(
                {
                    "index": index,
                    "title": title,
                    "url": url,
                    "content": answer_text,
                }
            )

            # حفظ النتيجة الخام في قاعدة المعرفة.
            if title and url:

                save_result = knowledge.learn(
                    title=title,
                    content=answer_text,
                    source=url,
                    knowledge_type="web_unverified"
                )

                if save_result.get(
                    "status"
                ) in (
                    "learned",
                    "duplicate"
                ):
                    saved_count += 1

        if not source_items:
            return None

        # ======================================================
        # Gemini Web Processing
        # ======================================================

        gemini_response = self._process_web_results_with_gemini(
            question,
            source_items
        )

        if gemini_response:

            final_response = gemini_response

        else:

            # مسار احتياطي إذا لم يعمل Gemini.
            response_sections = []

            for item in source_items:

                response_sections.append(
                    f"المصدر {item['index']}:\n"
                    f"{item['title']}\n"
                    f"{item['content']}\n"
                    f"الرابط: {item['url']}"
                )

            final_response = (
                "بحثت تلقائيًا في الويب لأن قاعدة المعرفة "
                "الحالية لم تحتوي على إجابة كافية.\n\n"
                + "\n\n".join(response_sections)
            )

        final_response += (
            "\n\n"
            "حالة الأدلة: معلومات مسترجعة من الويب "
            "ولم يتم التحقق منها علميًا بعد."
        )

        if previous_memories:

            final_response += (
                "\n\n"
                + self._build_memory_response(
                    previous_memories
                )
            )

        # حفظ نتيجة البحث في الذاكرة العلمية
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
            "scientific_memory_matches":
                len(previous_memories),
            "web_search_used": True,
            "web_results":
                len(source_items),
            "knowledge_saved":
                saved_count,
            "gemini_used":
                bool(gemini_response),
            "evidence_status":
                "web_unverified",
            "evidence_confidence":
                "low",
            "scientific_policy_version":
                scientific_policy_version(),
            "scientific_rules_active":
                len(self.scientific_rules),
            "security_confirmation_required":
                security.requires_confirmation()
        }

    # ==========================================================
    # Gemini Web Processing
    # ==========================================================

    def _process_web_results_with_gemini(
        self,
        question: str,
        source_items
    ):
        """
        يرسل نتائج البحث الموجودة بالفعل إلى Gemini
        لكي يحولها إلى إجابة مفهومة بلغة المستخدم.

        Gemini هنا لا يبحث في الويب.
        DRAGON هو الذي يبحث، ثم Gemini يعالج النتائج.
        """

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            return None

        if not source_items:
            return None

        language_instruction = self._detect_response_language(
            question
        )

        source_blocks = []

        for item in source_items:

            source_blocks.append(
                (
                    f"المصدر {item['index']}:\n"
                    f"العنوان: {item['title']}\n"
                    f"الرابط: {item['url']}\n"
                    f"المحتوى:\n{item['content']}"
                )
            )

        sources_text = "\n\n---\n\n".join(
            source_blocks
        )

        prompt = f"""
أنت وحدة معالجة المعرفة داخل نظام DRAGON AI CORE.

مهمتك هي معالجة نتائج بحث الويب التي قدمها لك النظام
والإجابة عن سؤال المستخدم اعتمادًا على هذه النتائج فقط.

سؤال المستخدم:
{question}

لغة الإجابة المطلوبة:
{language_instruction}

القواعد الإلزامية:

1. أجب بلغة سؤال المستخدم.
2. إذا كان السؤال بالعربية، أجب بالعربية.
3. لا تعرض نصوص صفحات الويب الخام كاملة.
4. لخّص المعلومات المهمة واشرحها بوضوح.
5. اجمع المعلومات المتوافقة بين المصادر.
6. إذا اختلفت المصادر، اذكر وجود الاختلاف ولا تخترع حسمًا.
7. لا تضف معلومة غير موجودة في المصادر المقدمة.
8. لا تخترع أرقامًا أو تواريخ أو أسماء أو مصادر.
9. لا تدّعي أن المعلومات مؤكدة علميًا.
10. لا تستخدم معرفة Gemini الخارجية لتعويض نقص المصادر.
11. اذكر المصادر المستخدمة في نهاية الإجابة.
12. حافظ على الروابط كما وردت.
13. اجعل الإجابة مباشرة ومنظمة.
14. لا تقل إنك بحثت بنفسك في الإنترنت؛ البحث قام به DRAGON.
15. لا تستخدم Markdown معقدًا. العناوين والنقاط البسيطة كافية.

نتائج البحث:

{sources_text}
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1800
            }
        }

        try:

            response = requests.post(
                GEMINI_API_URL,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=GEMINI_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            candidates = data.get(
                "candidates",
                []
            )

            if not candidates:
                return None

            content = candidates[0].get(
                "content",
                {}
            )

            parts = content.get(
                "parts",
                []
            )

            generated_parts = []

            for part in parts:

                text = part.get(
                    "text",
                    ""
                )

                if text:
                    generated_parts.append(
                        str(text).strip()
                    )

            final_text = "\n".join(
                part
                for part in generated_parts
                if part
            ).strip()

            if not final_text:
                return None

            return final_text

        except requests.RequestException:
            return None

        except ValueError:
            return None

        except Exception:
            return None

    # ==========================================================
    # Response Language Detection
    # ==========================================================

    def _detect_response_language(
        self,
        question: str
    ) -> str:
        """
        يحدد لغة الإجابة المطلوبة من لغة سؤال المستخدم.
        """

        arabic_characters = 0
        latin_characters = 0

        for char in question:

            if "\u0600" <= char <= "\u06ff":
                arabic_characters += 1

            elif (
                "a" <= char.lower() <= "z"
            ):
                latin_characters += 1

        if arabic_characters > latin_characters:
            return "العربية"

        if latin_characters > 0:
            return (
                "نفس لغة السؤال. "
                "إذا كان السؤال بالإنجليزية فأجب بالإنجليزية."
            )

        return "لغة السؤال نفسها"

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
            "learning_engine": "manual_learning",
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
                    "صيغة التعلم الذاتي غير صحيحة. "
                    "استخدم: تعلم ذاتي | العنوان | المحتوى | "
                    "المصدر | fact/inference/hypothesis"
                )
            }

        _, title, content, source, knowledge_type = parts

        result = self_learning.learn(
            title=title,
            content=content,
            source=source,
            knowledge_type=knowledge_type
        )

        return {
            "status": result["status"],
            "learning": result,
            "learning_engine": "self_learning",
            "scientific_policy_version":
                scientific_policy_version(),
            "scientific_rules_active":
                len(self.scientific_rules),
            "security_confirmation_required":
                security.requires_confirmation()
        }

    # ==========================================================
    # Web Learning
    # ==========================================================

    def _process_web_learning_command(
        self,
        message: str
    ) -> dict:

        parts = [
            part.strip()
            for part in message.split("|")
        ]

        if len(parts) != 4:
            return {
                "status": "error",
                "message": (
                    "صيغة التعلم من الويب غير صحيحة. "
                    "استخدم: "
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

        return {
            "status": result.get(
                "status",
                "unknown"
            ),
            "learning_engine": "web_learning",
            "learning": result,
            "scientific_policy_version":
                scientific_policy_version(),
            "scientific_rules_active":
                len(self.scientific_rules),
            "security_confirmation_required":
                security.requires_confirmation()
        }

    # ==========================================================
    # Natural Learning
    # ==========================================================

    def _process_natural_learning(
        self,
        message: str
    ) -> dict:

        content = message[
            len("تعلم أن "):
        ].strip()

        if not content:
            return {
                "status": "error",
                "message": (
                    "لم تحدد المعلومة التي تريد أن أتعلمها."
                )
            }

        result = knowledge.learn(
            title="معلومة متعلمة",
            content=content,
            source="user-natural-learning",
            knowledge_type="fact"
        )

        if result["status"] == "learned":
            response = (
                "تم تعلم المعلومة وحفظها في قاعدة المعرفة."
            )

        elif result["status"] == "duplicate":
            response = (
                "هذه المعلومة موجودة بالفعل "
                "في قاعدة المعرفة."
            )

        else:
            response = (
                "لم يتم حفظ المعلومة."
            )

        return {
            "status": result["status"],
            "response": response,
            "learning": result,
            "learning_engine": "natural_learning",
            "scientific_policy_version":
                scientific_policy_version(),
            "scientific_rules_active":
                len(self.scientific_rules),
            "security_confirmation_required":
                security.requires_confirmation()
        }

    # ==========================================================
    # Response Generation
    # ==========================================================

    def _generate_response(
        self,
        message,
        knowledge_results,
        previous_memories
    ):

        # ------------------------------------------------------
        # No Knowledge
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # Conceptual Comparison
        # ------------------------------------------------------

        if self._is_conceptual_question(message):

            return self._build_conceptual_response(
                message,
                knowledge_results
            )

        # ------------------------------------------------------
        # Single Result
        # ------------------------------------------------------

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

        # ------------------------------------------------------
        # Multiple Results
        # ------------------------------------------------------

        selected_results = self._select_best_results(
            knowledge_results
        )

        sections = []

        facts_count = 0
        inference_count = 0
        hypothesis_count = 0

        for index, result in enumerate(
            selected_results,
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
            "وجدت معلومات مرتبطة بالسؤال:\n\n"
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

    # ==========================================================
    # Conceptual Question Detection
    # ==========================================================

    def _is_conceptual_question(
        self,
        message: str
    ) -> bool:

        normalized = message.strip().lower()

        conceptual_patterns = (
            "ما الفرق بين",
            "ما هو الفرق بين",
            "ماهي الفرق بين",
            "ما الفرق",
            "ما معنى",
            "ماذا يعني",
            "ما هو",
            "ما هي",
            "اشرح الفرق",
            "قارن بين",
            "مقارنة بين",
        )

        return any(
            pattern in normalized
            for pattern in conceptual_patterns
        )

    # ==========================================================
    # Conceptual Response
    # ==========================================================

    def _build_conceptual_response(
        self,
        message,
        knowledge_results
    ):

        selected = self._select_conceptual_results(
            knowledge_results
        )

        if not selected:
            return (
                "السؤال مفاهيمي، لكن لا توجد معلومات "
                "كافية في قاعدة المعرفة الحالية للإجابة عليه."
            ), {
                "evidence_status": "not_applicable",
                "confidence": "not_applicable"
            }

        sections = []

        for result in selected:

            sections.append(
                f"• {result.title}\n"
                f"{result.content}\n"
                f"نوع المعرفة: {result.knowledge_type}\n"
                f"المصدر: {result.source}"
            )

        response = (
            "إجابة مفاهيمية اعتمادًا على المعرفة المسجلة:\n\n"
            + "\n\n".join(sections)
        )

        response += (
            "\n\n"
            "ملاحظة: هذا السؤال يطلب مقارنة أو تعريفًا "
            "مفاهيميًا، لذلك لا أتعامل معه كتقييم لقوة "
            "الأدلة التجريبية."
        )

        return response, {
            "evidence_status": "not_applicable",
            "confidence": "not_applicable"
        }

    # ==========================================================
    # Result Selection
    # ==========================================================

    def _select_best_results(
        self,
        results,
        limit: int = 5
    ):

        if len(results) <= limit:
            return results

        return results[:limit]

    # ==========================================================
    # Conceptual Result Selection
    # ==========================================================

    def _select_conceptual_results(
        self,
        results
    ):

        # نعطي أولوية للمصادر العلمية الداخلية
        internal_scientific = [
            result
            for result in results
            if result.source == "internal-scientific"
        ]

        if internal_scientific:
            results = internal_scientific

        # نضمن عدم تكرار نفس نوع المعرفة
        selected = []

        used_types = set()

        for result in results:

            knowledge_type = result.knowledge_type

            if knowledge_type not in used_types:
                selected.append(result)
                used_types.add(knowledge_type)

        # إذا كانت لدينا نتائج إضافية مفيدة
        # نسمح بها حتى ثلاثة عناصر فقط.
        if len(selected) < 3:

            for result in results:

                if result in selected:
                    continue

                selected.append(result)

                if len(selected) >= 3:
                    break

        return selected[:3]

    # ==========================================================
    # Memory Response
    # ==========================================================

    def _build_memory_response(
        self,
        previous_memories
    ):

        if not previous_memories:
            return ""

        latest_memory = previous_memories[-1]

        content = latest_memory.content.strip()

        # منع تضخم الذاكرة داخل الرد
        max_memory_length = 700

        if len(content) > max_memory_length:
            content = (
                content[:max_memory_length].rstrip()
                + "..."
            )

        return (
            "من الذاكرة العلمية السابقة:\n"
            f"{content}\n"
            f"حالة الأدلة السابقة: "
            f"{latest_memory.evidence_status or 'غير محددة'}\n"
            f"درجة الثقة السابقة: "
            f"{latest_memory.confidence or 'غير محددة'}"
        )

    # ==========================================================
    # Scientific Assessment
    # ==========================================================

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

    # ==========================================================
    # Scientific Policy
    # ==========================================================

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

        elif knowledge_type == "web_unverified":

            policy_note = (
                "الحالة العلمية: معلومات مسترجعة من الويب "
                "ولم يتم التحقق منها علميًا بعد."
            )

        else:

            policy_note = (
                "الحالة العلمية: نوع المعرفة غير معروف."
            )

        return f"{response}\n{policy_note}"


dragon_engine = DragonEngine()
