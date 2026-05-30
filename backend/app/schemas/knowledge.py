from pydantic import BaseModel


class KnowledgeCreateRequest(BaseModel):
    title: str
    category: str
    keywords: list[str]
    content: str
