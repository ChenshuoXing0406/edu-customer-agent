import os
from secrets import compare_digest

from fastapi import Request
from fastapi.responses import RedirectResponse


ADMIN_SESSION_KEY = "admin_authenticated"


def get_admin_credentials() -> tuple[str, str]:
    return (
        os.getenv("ADMIN_USERNAME") or "admin",
        os.getenv("ADMIN_PASSWORD") or "admin123",
    )


def credentials_are_valid(username: str, password: str) -> bool:
    expected_username, expected_password = get_admin_credentials()

    return compare_digest(username.encode(), expected_username.encode()) and compare_digest(
        password.encode(),
        expected_password.encode(),
    )


def is_admin_authenticated(request: Request) -> bool:
    return request.session.get(ADMIN_SESSION_KEY) is True


def require_admin(request: Request) -> RedirectResponse | None:
    if is_admin_authenticated(request):
        return None

    return RedirectResponse("/login", status_code=303)


def login_admin(request: Request) -> None:
    request.session[ADMIN_SESSION_KEY] = True


def logout_admin(request: Request) -> None:
    request.session.clear()
