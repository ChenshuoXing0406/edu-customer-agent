from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api import admin, analytics, chat, feedback, knowledge, tickets
from app.core.config import SESSION_SECRET_KEY
from app.core.database import initialize_database


initialize_database()
app = FastAPI(title="Edu Customer Agent")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax",
)

app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(tickets.router)
app.include_router(knowledge.router)
app.include_router(feedback.router)
app.include_router(analytics.router)
