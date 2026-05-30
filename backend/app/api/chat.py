from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import create_chat_response


router = APIRouter()


@router.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return create_chat_response(req)
