from pydantic import BaseModel


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    intent: str
    need_handoff: bool
    sources: list[str]
    conversation_id: str
