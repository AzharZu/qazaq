import hashlib
import hmac
import secrets
import time
from typing import Optional

from fastapi import Request, Response
from passlib.context import CryptContext
from passlib.exc import UnknownHashError

from .config import get_settings

# Use pbkdf2_sha256 only to avoid bcrypt backend issues in some environments.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
settings = get_settings()

SESSION_MAX_AGE = 60 * 60 * 24 * 14  # 14 days
AUTH_COOKIE_NAME = "session"


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


def _sign(payload: str) -> str:
    return hmac.new(settings.secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def build_session_token(user_id: int, issued_at: Optional[int] = None) -> str:
    ts = issued_at or int(time.time())
    nonce = secrets.token_hex(8)
    payload = f"{user_id}:{ts}:{nonce}"
    signature = _sign(payload)
    return f"{payload}:{signature}"


def parse_session_token(token: str) -> Optional[int]:
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


def attach_session_cookie(response: Response, session_token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=session_token,
        httponly=True,
        max_age=SESSION_MAX_AGE,
        expires=SESSION_MAX_AGE,
        secure=False,  # local dev
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")


def get_user_id_from_request(request: Request) -> Optional[int]:
    token = (
        request.cookies.get(AUTH_COOKIE_NAME)
        or request.cookies.get("qazaq_session")
        or request.cookies.get("qazaq_state")
    )
    # Bearer token support for SPA/localStorage flows
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    return parse_session_token(token)
