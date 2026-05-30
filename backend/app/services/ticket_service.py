from datetime import datetime

from sqlalchemy import select

from app.core.database import session_scope
from app.models import Conversation, HandoffTicket, UnansweredQuestion


def format_time(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def serialize_conversation(item: Conversation) -> dict:
    result = {
        "conversation_id": item.conversation_id,
        "time": format_time(item.created_at),
        "user_id": item.user_id,
        "user_message": item.user_message,
        "assistant_answer": item.assistant_answer,
        "intent": item.intent,
        "need_handoff": item.need_handoff,
        "sources": item.sources,
        "feedback": item.feedback,
    }

    if item.feedback_time is not None:
        result["feedback_time"] = format_time(item.feedback_time)

    return result


def serialize_handoff_ticket(item: HandoffTicket) -> dict:
    result = {
        "ticket_id": item.ticket_id,
        "time": format_time(item.created_at),
        "status": item.status,
        "user_id": item.user_id,
        "intent": item.intent,
        "reason": item.reason,
        "user_message": item.user_message,
        "assistant_answer": item.assistant_answer,
        "sources": item.sources,
    }

    if item.resolved_time is not None:
        result["resolved_time"] = format_time(item.resolved_time)

    return result


def serialize_unanswered_question(item: UnansweredQuestion) -> dict:
    return {
        "time": format_time(item.created_at),
        "user_id": item.user_id,
        "message": item.message,
        "intent": item.intent,
        "status": item.status,
    }


def list_conversations() -> list[dict]:
    with session_scope() as session:
        items = session.scalars(select(Conversation).order_by(Conversation.id)).all()
        return [serialize_conversation(item) for item in items]


def save_conversation_record(
    user_id: str,
    user_message: str,
    answer: str,
    intent: str,
    need_handoff: bool,
    sources: list[str],
) -> str:
    with session_scope() as session:
        conversation_count = len(session.scalars(select(Conversation.id)).all())
        conversation_id = f"CHAT-{conversation_count + 1:04d}"
        session.add(
            Conversation(
                conversation_id=conversation_id,
                user_id=user_id,
                user_message=user_message,
                assistant_answer=answer,
                intent=intent,
                need_handoff=need_handoff,
                sources=sources,
            )
        )

    return conversation_id


def list_handoff_tickets() -> list[dict]:
    with session_scope() as session:
        items = session.scalars(select(HandoffTicket).order_by(HandoffTicket.id)).all()
        return [serialize_handoff_ticket(item) for item in items]


def create_handoff_ticket(
    user_id: str,
    user_message: str,
    answer: str,
    intent: str,
    reason: str,
    sources: list[str],
) -> None:
    with session_scope() as session:
        ticket_count = len(session.scalars(select(HandoffTicket.id)).all())
        session.add(
            HandoffTicket(
                ticket_id=f"TICKET-{ticket_count + 1:04d}",
                status="open",
                user_id=user_id,
                intent=intent,
                reason=reason,
                user_message=user_message,
                assistant_answer=answer,
                sources=sources,
            )
        )


def resolve_handoff_ticket(ticket_id: str) -> dict:
    with session_scope() as session:
        ticket = session.scalar(
            select(HandoffTicket).where(HandoffTicket.ticket_id == ticket_id)
        )

        if ticket is None:
            return {
                "message": "ticket_not_found",
                "ticket_id": ticket_id,
            }

        ticket.status = "resolved"
        ticket.resolved_time = datetime.now()

        return {
            "message": "ticket_resolved",
            "ticket": serialize_handoff_ticket(ticket),
        }


def list_unanswered_questions() -> list[dict]:
    with session_scope() as session:
        items = session.scalars(
            select(UnansweredQuestion).order_by(UnansweredQuestion.id)
        ).all()
        return [serialize_unanswered_question(item) for item in items]


def save_unanswered_question(user_id: str, message: str, intent: str) -> None:
    with session_scope() as session:
        session.add(
            UnansweredQuestion(
                user_id=user_id,
                message=message,
                intent=intent,
                status="waiting_for_knowledge_update",
            )
        )
