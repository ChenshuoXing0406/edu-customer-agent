from sqlalchemy import select

from app.core.database import session_scope
from app.models import Conversation, HandoffTicket, UnansweredQuestion


def get_analytics_stats() -> dict:
    with session_scope() as session:
        conversations = session.scalars(select(Conversation)).all()
        tickets = session.scalars(select(HandoffTicket)).all()
        unanswered = session.scalars(select(UnansweredQuestion)).all()

    total_conversations = len(conversations)
    handoff_count = len([item for item in conversations if item.need_handoff])
    auto_resolved_count = len([item for item in conversations if not item.need_handoff])

    if total_conversations == 0:
        handoff_rate = 0
        auto_resolved_rate = 0
    else:
        handoff_rate = round(handoff_count / total_conversations * 100, 2)
        auto_resolved_rate = round(auto_resolved_count / total_conversations * 100, 2)

    intent_counts = {}

    for item in conversations:
        intent = item.intent or "unknown"
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    unanswered_question_counts = {}

    for item in unanswered:
        unanswered_question_counts[item.message] = (
            unanswered_question_counts.get(item.message, 0) + 1
        )

    top_unanswered = [
        {
            "message": message,
            "count": count,
        }
        for message, count in unanswered_question_counts.items()
    ]

    top_unanswered.sort(key=lambda item: item["count"], reverse=True)

    open_tickets = len([item for item in tickets if item.status != "resolved"])
    resolved_tickets = len([item for item in tickets if item.status == "resolved"])

    return {
        "total_conversations": total_conversations,
        "auto_resolved_count": auto_resolved_count,
        "handoff_count": handoff_count,
        "auto_resolved_rate": auto_resolved_rate,
        "handoff_rate": handoff_rate,
        "unanswered_count": len(unanswered),
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "intent_counts": intent_counts,
        "top_unanswered": top_unanswered[:10],
    }
