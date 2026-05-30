from sqlalchemy import delete

from app.core.database import session_scope
from app.models import KnowledgeItem


def test_python_course_retrieval(client):
    response = client.post(
        "/api/chat",
        json={
            "user_id": "retrieval-python",
            "message": "Python 课程适合零基础吗？",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["intent"] == "course_consultation"
    assert result["need_handoff"] is False
    assert result["sources"] == ["Python 零基础就业班课程介绍"]


def test_ai_course_price_retrieval(client):
    response = client.post(
        "/api/chat",
        json={
            "user_id": "retrieval-ai-price",
            "message": "AI 大模型课程多少钱？",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["intent"] == "price_consultation"
    assert result["need_handoff"] is False
    assert result["sources"] == [
        "AI 大模型应用开发课课程介绍",
        "课程价格与优惠政策",
    ]


def test_refund_policy_retrieval(client):
    response = client.post(
        "/api/chat",
        json={
            "user_id": "retrieval-refund",
            "message": "报名后可以退款吗？",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["intent"] == "refund_policy"
    assert result["need_handoff"] is True
    assert result["sources"] == ["退款与转班政策"]


def test_japanese_course_miss_then_hit_after_knowledge_creation(client):
    with session_scope() as session:
        session.execute(
            delete(KnowledgeItem).where(KnowledgeItem.title.contains("日语"))
        )

    question = "你们有没有日语课程？"
    response = client.post(
        "/api/chat",
        json={
            "user_id": "retrieval-japanese",
            "message": question,
        },
    )

    assert response.status_code == 200
    missed_result = response.json()
    assert missed_result["intent"] == "course_consultation"
    assert missed_result["need_handoff"] is True
    assert missed_result["sources"] == []

    unanswered = client.get("/api/unanswered-questions").json()
    assert len(unanswered) == 1
    assert unanswered[0]["message"] == question

    create_response = client.post(
        "/api/knowledge",
        json={
            "title": "日语入门课程介绍",
            "category": "course",
            "keywords": ["日语", "日语课程", "零基础", "入门", "课程"],
            "content": "日语入门课程适合零基础学员，从五十音图开始学习。",
        },
    )

    assert create_response.status_code == 200
    assert create_response.json()["message"] == "knowledge_created"

    response = client.post(
        "/api/chat",
        json={
            "user_id": "retrieval-japanese",
            "message": question,
        },
    )

    assert response.status_code == 200
    matched_result = response.json()
    assert matched_result["need_handoff"] is False
    assert matched_result["sources"] == ["日语入门课程介绍"]

    unanswered = client.get("/api/unanswered-questions").json()
    assert len(unanswered) == 1
