from types import SimpleNamespace
from unittest.mock import Mock

from app.services import llm_service


def test_chat_falls_back_to_rule_answer_without_api_key(client, monkeypatch):
    openai_client = Mock()
    monkeypatch.setattr(llm_service, "OpenAI", openai_client)

    response = client.post(
        "/api/chat",
        json={
            "user_id": "rule-fallback",
            "message": "Python 课程适合零基础吗？",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"].startswith("根据课程知识库")
    openai_client.assert_not_called()


def test_chat_uses_llm_when_configured(client, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    completion = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="这是一条严格基于知识库生成的课程回答。")
            )
        ]
    )
    create_completion = Mock(return_value=completion)
    openai_client = Mock()
    openai_client.return_value.chat.completions.create = create_completion
    monkeypatch.setattr(llm_service, "OpenAI", openai_client)

    response = client.post(
        "/api/chat",
        json={
            "user_id": "llm-user",
            "message": "Python 课程适合零基础吗？",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "这是一条严格基于知识库生成的课程回答。"
    openai_client.assert_called_once_with(
        api_key="test-api-key",
        base_url="https://llm.example.test/v1",
        timeout=15.0,
    )

    request = create_completion.call_args.kwargs
    assert request["model"] == "test-model"
    assert request["temperature"] == 0
    assert "只能根据提供的知识库内容回答" in request["messages"][0]["content"]
    assert "Python 零基础就业班课程介绍" in request["messages"][1]["content"]
    assert "请严格根据上述知识库内容回答用户" in request["messages"][1]["content"]


def test_chat_falls_back_to_rule_answer_when_llm_fails(client, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setattr(llm_service, "OpenAI", Mock(side_effect=RuntimeError("offline")))

    response = client.post(
        "/api/chat",
        json={
            "user_id": "llm-failure",
            "message": "Python",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"].startswith("根据课程知识库")


def test_chat_skips_llm_and_suggests_handoff_without_knowledge(client, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    openai_client = Mock()
    monkeypatch.setattr(llm_service, "OpenAI", openai_client)

    response = client.post(
        "/api/chat",
        json={
            "user_id": "unknown-question",
            "message": "martian language",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["need_handoff"] is True
    assert result["sources"] == []
    assert "建议转人工客服" in result["answer"]
    openai_client.assert_not_called()

    unanswered = client.get("/api/unanswered-questions").json()
    assert len(unanswered) == 1


def test_llm_answer_adds_handoff_recommendation_for_sensitive_question(
    client,
    monkeypatch,
):
    monkeypatch.setenv("LLM_API_KEY", "test-api-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    completion = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="报名后 7 天内可以申请退款。")
            )
        ]
    )
    openai_client = Mock()
    openai_client.return_value.chat.completions.create = Mock(return_value=completion)
    monkeypatch.setattr(llm_service, "OpenAI", openai_client)

    response = client.post(
        "/api/chat",
        json={
            "user_id": "sensitive-question",
            "message": "报名后可以退款吗？",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["need_handoff"] is True
    assert "建议转人工客服" in result["answer"]
