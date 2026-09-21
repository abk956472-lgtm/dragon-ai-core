"""
DRAGON AI CORE
Scientific Intelligence Policy
"""

SCIENTIFIC_POLICY_VERSION = "1.1.0"


SCIENTIFIC_RULES = [
    "Do not fabricate scientific sources, studies, experiments, or results.",
    "Distinguish facts from inference, hypothesis, and speculation.",
    "State uncertainty when evidence is incomplete or disputed.",
    "Do not present a hypothesis as an established fact.",
    "Do not manipulate data to support a desired conclusion.",
    "Identify important assumptions and limitations.",
    "Do not claim to have used tools, sources, experiments, or data that were not actually used.",
    "When evidence is insufficient, say that the available information is insufficient.",
    "Distinguish scientific evidence from opinion or personal interpretation.",
    "Prefer reproducible and verifiable information.",
]


def get_scientific_rules():
    return SCIENTIFIC_RULES.copy()


def scientific_policy_version():
    return SCIENTIFIC_POLICY_VERSION


def evaluate_evidence(
    facts_count: int,
    inference_count: int,
    hypothesis_count: int
) -> dict:
    """
    تقييم أولي لقوة الأدلة العلمية المتاحة.
    هذا التقييم لا يثبت صحة أي استنتاج علمي.
    """

    # الحقيقة المسجلة في قاعدة المعرفة
    # تبقى حقيقة معرفية، لكن ذلك لا يعني
    # إثبات ادعاء علمي جديد.
    if facts_count > 0 and inference_count == 0 and hypothesis_count == 0:
        return {
            "evidence_status": "available",
            "confidence": "moderate",
            "reason": (
                "توجد حقيقة مسجلة في قاعدة المعرفة. "
                "هذا يصف حالة المعرفة المسجلة ولا يعني "
                "إثبات استنتاج علمي جديد."
            )
        }

    if facts_count == 0:
        return {
            "evidence_status": "insufficient",
            "confidence": "low",
            "reason": (
                "لا توجد حقائق مسجلة كافية لبناء "
                "استنتاج علمي."
            )
        }

    if hypothesis_count > 0 and facts_count == 1:
        return {
            "evidence_status": "limited",
            "confidence": "low",
            "reason": (
                "توجد حقيقة واحدة مع فرضية، "
                "وهذا لا يكفي لإثبات علاقة علمية جديدة."
            )
        }

    if facts_count >= 2:
        return {
            "evidence_status": "available",
            "confidence": "moderate",
            "reason": (
                "توجد عدة حقائق يمكن استخدامها "
                "لبناء تحليل أولي، مع ضرورة التحقق "
                "من العلاقة بينها."
            )
        }

    if inference_count > 0:
        return {
            "evidence_status": "inference_only",
            "confidence": "low",
            "reason": (
                "المعلومات تتضمن استنتاجات سابقة، "
                "ولا ينبغي اعتبارها حقائق مستقلة."
            )
        }

    return {
        "evidence_status": "insufficient",
        "confidence": "low",
        "reason": (
            "الأدلة الحالية غير كافية لإصدار "
            "استنتاج علمي موثوق."
        )
    }
