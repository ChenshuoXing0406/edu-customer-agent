from app.schemas.chat import ChatRequest, ChatResponse
from app.services.knowledge_service import retrieve_knowledge
from app.services.llm_service import generate_llm_answer
from app.services.ticket_service import (
    create_handoff_ticket,
    save_conversation_record,
    save_unanswered_question,
)


def detect_intent(message: str) -> str:
    text = message.lower()

    if "价格" in text or "多少钱" in text or "费用" in text or "学费" in text:
        return "price_consultation"

    if "试听" in text or "体验课" in text or "预约" in text:
        return "trial_booking"

    if "退款" in text or "退费" in text or "不想学" in text or "退课" in text:
        return "refund_policy"

    if "登录" in text or "账号" in text or "密码" in text or "验证码" in text:
        return "account_issue"

    if "证书" in text or "结业" in text:
        return "certificate_issue"

    if "人工" in text or "真人" in text or "客服" in text or "投诉" in text:
        return "human_service"

    if "python" in text or "ai" in text or "大模型" in text or "课程" in text or "零基础" in text:
        return "course_consultation"

    return "other"


def should_handoff(message: str, intent: str, matched_docs: list[dict]) -> bool:
    text = message.lower()

    handoff_keywords = [
        "人工",
        "真人",
        "投诉",
        "差评",
        "被骗",
        "退费",
        "退款",
        "不满意",
        "生气",
    ]

    if intent == "human_service":
        return True

    if intent == "refund_policy":
        return True

    if any(keyword in text for keyword in handoff_keywords):
        return True

    if len(matched_docs) == 0:
        return True

    return False


def get_handoff_reason(message: str, intent: str, matched_docs: list[dict]) -> str:
    if intent == "refund_policy":
        return "退款或退费问题，需要人工确认报名时间、学习进度和退款规则"

    if intent == "human_service":
        return "用户明确要求人工客服"

    if len(matched_docs) == 0:
        return "知识库未命中，需要人工补充或确认"

    if "投诉" in message or "差评" in message or "被骗" in message:
        return "用户存在投诉或强烈负面情绪"

    return "需要人工进一步确认"


def generate_rule_answer(
    message: str,
    intent: str,
    matched_docs: list[dict],
    need_handoff: bool,
) -> str:
    if len(matched_docs) == 0:
        return (
            "我暂时没有在课程知识库中找到足够准确的信息。"
            "为了避免误导你，建议转人工客服进一步确认。"
        )

    context_parts = []
    for doc in matched_docs:
        context_parts.append(f"【{doc['title']}】{doc['content']}")

    context = "\n".join(context_parts)

    if need_handoff:
        return (
            "我先根据知识库帮你说明：\n\n"
            f"{context}\n\n"
            "这个问题可能涉及人工确认或敏感服务流程，我建议为你转接人工客服继续处理。"
        )

    return (
        "根据课程知识库，我为你查到：\n\n"
        f"{context}\n\n"
        "你还可以继续问我课程适合人群、价格、试听、报名、退款或证书相关问题。"
    )


def generate_answer(
    message: str,
    intent: str,
    matched_docs: list[dict],
    need_handoff: bool,
) -> str:
    try:
        llm_answer = generate_llm_answer(
            message=message,
            intent=intent,
            matched_docs=matched_docs,
            need_handoff=need_handoff,
        )
    except Exception:
        llm_answer = None

    if llm_answer:
        return llm_answer

    return generate_rule_answer(message, intent, matched_docs, need_handoff)


def create_chat_response(req: ChatRequest) -> ChatResponse:
    intent = detect_intent(req.message)
    matched_docs = retrieve_knowledge(req.message, intent)
    need_handoff = should_handoff(req.message, intent, matched_docs)
    answer = generate_answer(req.message, intent, matched_docs, need_handoff)
    sources = [doc["title"] for doc in matched_docs]

    conversation_id = save_conversation_record(
        user_id=req.user_id,
        user_message=req.message,
        answer=answer,
        intent=intent,
        need_handoff=need_handoff,
        sources=sources,
    )

    if len(matched_docs) == 0:
        save_unanswered_question(
            user_id=req.user_id,
            message=req.message,
            intent=intent,
        )

    if need_handoff:
        reason = get_handoff_reason(req.message, intent, matched_docs)

        create_handoff_ticket(
            user_id=req.user_id,
            user_message=req.message,
            answer=answer,
            intent=intent,
            reason=reason,
            sources=sources,
        )

    return ChatResponse(
        answer=answer,
        intent=intent,
        need_handoff=need_handoff,
        sources=sources,
        conversation_id=conversation_id,
    )
