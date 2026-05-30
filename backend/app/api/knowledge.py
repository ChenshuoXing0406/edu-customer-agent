from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from app.core.auth import require_admin
from app.core.config import STATIC_DIR
from app.schemas.knowledge import KnowledgeCreateRequest
from app.services.knowledge_service import create_knowledge, load_knowledge
from app.services.ticket_service import list_unanswered_questions


router = APIRouter()


@router.get("/knowledge-admin")
def knowledge_admin(request: Request):
    redirect = require_admin(request)

    if redirect:
        return redirect

    return FileResponse(STATIC_DIR / "knowledge.html")


@router.get("/api/unanswered-questions")
def unanswered_questions():
    return list_unanswered_questions()


@router.get("/api/knowledge")
def list_knowledge():
    return load_knowledge()


@router.post("/api/knowledge")
def add_knowledge(req: KnowledgeCreateRequest):
    return create_knowledge(req)
