import os

from openai import OpenAI


SYSTEM_PROMPT = """你是教育课程客服。
你只能根据提供的知识库内容回答，不允许使用知识库外的信息，不允许编造。
如果知识库不足以回答问题，必须明确说不知道，并建议转人工客服。
涉及退款、投诉、账号异常、人工请求时，在根据知识库说明后，必须建议转人工客服继续处理。
回答应简洁、自然，直接面向用户。"""


def get_llm_settings() -> tuple[str, str, str]:
    return (
        os.getenv("LLM_BASE_URL", "").strip(),
        os.getenv("LLM_API_KEY", "").strip(),
        os.getenv("LLM_MODEL", "").strip(),
    )


def is_llm_configured() -> bool:
    _, api_key, model = get_llm_settings()
    return bool(api_key and model)


def build_knowledge_context(matched_docs: list[dict]) -> str:
    return "\n\n".join(
        (
            f"标题：{doc['title']}\n"
            f"分类：{doc['category']}\n"
            f"内容：{doc['content']}"
        )
        for doc in matched_docs
    )


def generate_llm_answer(
    message: str,
    intent: str,
    matched_docs: list[dict],
    need_handoff: bool,
) -> str | None:
    if not matched_docs or not is_llm_configured():
        return None

    base_url, api_key, model = get_llm_settings()
    client_options = {
        "api_key": api_key,
        "timeout": 15.0,
    }

    if base_url:
        client_options["base_url"] = base_url

    client = OpenAI(**client_options)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"用户问题：{message}\n"
                    f"已识别意图：{intent}\n"
                    f"是否需要建议转人工：{'是' if need_handoff else '否'}\n\n"
                    "知识库内容：\n"
                    f"{build_knowledge_context(matched_docs)}\n\n"
                    "请严格根据上述知识库内容回答用户。"
                ),
            },
        ],
    )

    answer = response.choices[0].message.content

    if not answer:
        return None

    answer = answer.strip()

    if need_handoff and "人工" not in answer:
        answer += "\n\n这个问题需要人工进一步确认，建议转人工客服继续处理。"

    return answer
