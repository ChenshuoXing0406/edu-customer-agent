from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    conversation_id: str
    rating: str
