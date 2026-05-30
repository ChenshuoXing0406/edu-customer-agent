from fastapi import APIRouter

from app.schemas.feedback import FeedbackRequest
from app.services.feedback_service import get_feedback_stats, save_feedback


router = APIRouter()


@router.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    if req.rating not in ["up", "down"]:
        return {
            "message": "invalid_rating",
            "allowed": ["up", "down"],
        }

    return save_feedback(req.conversation_id, req.rating)


@router.get("/api/feedback-stats")
def feedback_stats():
    return get_feedback_stats()
