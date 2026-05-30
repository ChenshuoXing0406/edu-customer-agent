def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_and_conversation_list(client):
    response = client.post(
        "/api/chat",
        json={
            "user_id": "student-001",
            "message": "Python",
        },
    )

    assert response.status_code == 200
    chat = response.json()
    assert chat["conversation_id"] == "CHAT-0001"
    assert chat["intent"] == "course_consultation"
    assert chat["need_handoff"] is False
    assert len(chat["sources"]) == 1

    response = client.get("/api/conversations")

    assert response.status_code == 200
    conversations = response.json()
    assert len(conversations) == 1
    assert conversations[0]["conversation_id"] == chat["conversation_id"]
    assert conversations[0]["user_id"] == "student-001"
    assert conversations[0]["feedback"] is None
    assert "time" in conversations[0]


def test_handoff_ticket_list_and_resolve(client):
    chat_response = client.post(
        "/api/chat",
        json={
            "user_id": "student-002",
            "message": "martian language",
        },
    )

    assert chat_response.status_code == 200
    assert chat_response.json()["need_handoff"] is True

    response = client.get("/api/handoff-tickets")

    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) == 1
    assert tickets[0]["ticket_id"] == "TICKET-0001"
    assert tickets[0]["status"] == "open"

    response = client.post("/api/handoff-tickets/TICKET-0001/resolve")

    assert response.status_code == 200
    result = response.json()
    assert result["message"] == "ticket_resolved"
    assert result["ticket"]["status"] == "resolved"
    assert "resolved_time" in result["ticket"]


def test_knowledge_list_and_create(client):
    response = client.get("/api/knowledge")

    assert response.status_code == 200
    knowledge_items = response.json()
    assert len(knowledge_items) == 8

    response = client.post(
        "/api/knowledge",
        json={
            "title": "SQLAlchemy basics",
            "category": "course",
            "keywords": ["sqlalchemy", "orm"],
            "content": "A test-only course item.",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["message"] == "knowledge_created"
    assert result["item"]["id"] == "course_009"

    response = client.get("/api/knowledge")

    assert response.status_code == 200
    assert len(response.json()) == 9


def test_feedback_and_feedback_stats(client):
    chat = client.post(
        "/api/chat",
        json={
            "user_id": "student-003",
            "message": "Python",
        },
    ).json()

    response = client.post(
        "/api/feedback",
        json={
            "conversation_id": chat["conversation_id"],
            "rating": "up",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["message"] == "feedback_saved"
    assert result["conversation"]["feedback"] == "up"
    assert result["feedback"]["rating"] == "up"

    response = client.get("/api/feedback-stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_feedback": 1,
        "positive": 1,
        "negative": 0,
        "satisfaction_rate": 100.0,
    }


def test_analytics(client):
    client.post(
        "/api/chat",
        json={
            "user_id": "student-004",
            "message": "Python",
        },
    )
    client.post(
        "/api/chat",
        json={
            "user_id": "student-005",
            "message": "martian language",
        },
    )

    response = client.get("/api/analytics")

    assert response.status_code == 200
    analytics = response.json()
    assert analytics["total_conversations"] == 2
    assert analytics["auto_resolved_count"] == 1
    assert analytics["handoff_count"] == 1
    assert analytics["unanswered_count"] == 1
    assert analytics["open_tickets"] == 1
