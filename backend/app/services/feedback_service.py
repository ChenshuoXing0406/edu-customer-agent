from datetime import datetime

from sqlalchemy import select

from app.core.database import session_scope
from app.models import Conversation, Feedback
from app.services.ticket_service import format_time, serialize_conversation


def serialize_feedback(item: Feedback) -> dict:
    return {
        "time": format_time(item.created_at),
        "conversation_id": item.conversation_id,
        "rating": item.rating,
    }


def save_feedback(conversation_id: str, rating: str) -> dict:
    with session_scope() as session:
        conversation = session.scalar(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )

        if conversation is not None:
            conversation.feedback = rating
            conversation.feedback_time = datetime.now()

        feedback = Feedback(
            conversation_id=conversation_id,
            rating=rating,
        )
        session.add(feedback)
        session.flush()

        return {
            "message": "feedback_saved",
            "conversation": (
                serialize_conversation(conversation) if conversation is not None else None
            ),
            "feedback": serialize_feedback(feedback),
        }


def get_feedback_stats() -> dict:
    with session_scope() as session:
        conversations = session.scalars(
            select(Conversation).where(Conversation.feedback.in_(["up", "down"]))
        ).all()

    total = len(conversations)
    positive = len([item for item in conversations if item.feedback == "up"])
    negative = len([item for item in conversations if item.feedback == "down"])

    if total == 0:
        satisfaction_rate = 0
    else:
        satisfaction_rate = round(positive / total * 100, 2)

    return {
        "total_feedback": total,
        "positive": positive,
        "negative": negative,
        "satisfaction_rate": satisfaction_rate,
    }
