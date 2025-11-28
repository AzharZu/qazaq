import hashlib
import hmac
import secrets
import time
from typing import Optional

from fastapi import Request
from fastapi.responses import Response

from . import models
from .config import get_settings
from .database import SessionLocal

settings = get_settings()
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def _sign(payload: str) -> str:
    return hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _build_session_token(user_id: int, issued_at: Optional[int] = None) -> str:
    ts = issued_at or int(time.time())
    nonce = secrets.token_hex(8)
    payload = f"{user_id}:{ts}:{nonce}"
    signature = _sign(payload)
    return f"{payload}:{signature}"


def _parse_session_token(token: str) -> Optional[int]:
    try:
        user_id_str, issued_str, nonce, signature = token.split(":", 3)
        payload = f"{user_id_str}:{issued_str}:{nonce}"
        if not hmac.compare_digest(signature, _sign(payload)):
            return None
        issued_at = int(issued_str)
        if issued_at <= 0 or time.time() - issued_at > SESSION_MAX_AGE:
            return None
        return int(user_id_str)
    except Exception:
        return None


def create_session(user: models.User) -> str:
    return _build_session_token(user.id)


def attach_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        max_age=SESSION_MAX_AGE,
        expires=SESSION_MAX_AGE,
        secure=False,  # local dev only
        samesite="lax",
        path="/",
    )


def get_current_user_from_request(request: Request) -> models.User | None:
    token = request.cookies.get("session")
    if not token:
        return None
    user_id = _parse_session_token(token)
    if not user_id:
        return None
    db = SessionLocal()
    try:
        return db.get(models.User, user_id)
    finally:
        db.close()


def set_user_session(request: Request, user: models.User) -> str:
    if "session" in request.scope:
        # reset previous session payload to avoid oversized cookies
        request.session.clear()
        request.session["user_id"] = user.id
        request.session["age"] = user.age
        request.session["target"] = user.target
    return create_session(user)


def clear_user_session(request: Request) -> None:
    if "session" in request.scope:
        request.session.clear()
