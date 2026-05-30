from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse

from app.core.auth import (
    credentials_are_valid,
    is_admin_authenticated,
    login_admin,
    logout_admin,
    require_admin,
)
from app.core.config import STATIC_DIR
from app.services.ticket_service import list_conversations


router = APIRouter()


@router.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/login")
def login(request: Request):
    if is_admin_authenticated(request):
        return RedirectResponse("/admin", status_code=303)

    return FileResponse(STATIC_DIR / "login.html")


@router.post("/login")
async def submit_login(request: Request):
    form_data = parse_qs((await request.body()).decode("utf-8"))
    username = form_data.get("username", [""])[0]
    password = form_data.get("password", [""])[0]

    if not credentials_are_valid(username, password):
        return RedirectResponse("/login?error=1", status_code=303)

    login_admin(request)
    return RedirectResponse("/admin", status_code=303)


@router.get("/logout")
def logout(request: Request):
    logout_admin(request)
    return RedirectResponse("/login", status_code=303)


@router.get("/admin")
def admin(request: Request):
    redirect = require_admin(request)

    if redirect:
        return redirect

    return FileResponse(STATIC_DIR / "admin.html")


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/api/conversations")
def conversations():
    return list_conversations()
