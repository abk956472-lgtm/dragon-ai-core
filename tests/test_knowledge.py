import pytest
from dragon_core.knowledge import KnowledgeBase


def test_knowledge_base_in_memory():
    kb = KnowledgeBase()
    kb.clear()

    # Learn a fact
    res = kb.learn(
        title="اختبار الذكاء الاصطناعي",
        content="الذكاء الاصطناعي مجال يعنى بإنشاء أنظمة ذكية.",
        source="test-source",
        knowledge_type="fact"
    )
    assert res["status"] == "learned"

    # Search
    results = kb.search("الذكاء الاصطناعي")
    assert len(results) > 0
    assert results[0].title == "اختبار الذكاء الاصطناعي"

    # Duplicate learning
    res_dup = kb.learn(
        title="اختبار الذكاء الاصطناعي",
        content="الذكاء الاصطناعي مجال يعنى بإنشاء أنظمة ذكية.",
        source="test-source",
        knowledge_type="fact"
    )
    assert res_dup["status"] == "duplicate"
