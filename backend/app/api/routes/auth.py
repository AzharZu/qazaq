from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...api import deps
from ...core.security import attach_session_cookie, build_session_token, clear_session_cookie, verify_password
from ...schemas.user import AuthResponse, LoginPayload, UserCreate, UserOut
from ...services.progress_service import recommend_course_slug
from ...services.users_service import create_user, get_user_by_email
from ...core.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_session_response(user, request: Request) -> JSONResponse:
    session_token = build_session_token(user.id)
    settings = get_settings()
    is_admin = (user.role or "").lower() == "admin" or (user.email or "").lower() in (settings.admin_emails or [])
    user_payload = UserOut.model_validate(user).model_dump()
    if not user_payload.get("name"):
        user_payload["name"] = getattr(user, "full_name", None) or (user.email.split("@")[0] if user.email else None)
    user_payload["full_name"] = user_payload.get("full_name") or user_payload.get("name")
    user_payload["role"] = user.role
    user_payload["is_admin"] = is_admin
    response = JSONResponse({"token": session_token, "user": user_payload})
    attach_session_cookie(response, session_token)
    request.session["course_slug"] = recommend_course_slug(user.age, user.target, getattr(user, "level", None))
    return response


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, request: Request, db: Session = Depends(deps.current_db)):
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = create_user(db, payload)
    return _issue_session_response(user, request)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, request: Request, db: Session = Depends(deps.current_db)):
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = create_user(db, payload)
    return _issue_session_response(user, request)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginPayload, request: Request, db: Session = Depends(deps.current_db)):
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    return _issue_session_response(user, request)


@router.post("/logout")
def logout(request: Request):
    response = JSONResponse({"ok": True})
    clear_session_cookie(response)
    request.session.clear()
    return response


@router.get("/me", response_model=UserOut)
def me(request: Request, db: Session = Depends(deps.current_db)):
    user = deps.get_current_user(request, db=db, allow_anonymous=False)
    settings = get_settings()
    is_admin = (user.role or "").lower() == "admin" or (user.email or "").lower() in (settings.admin_emails or [])
    payload = UserOut.model_validate(user).model_dump()
    if not payload.get("name"):
        payload["name"] = getattr(user, "full_name", None) or (user.email.split("@")[0] if user.email else None)
    payload["full_name"] = payload.get("full_name") or payload.get("name")
    payload["role"] = user.role
    payload["is_admin"] = is_admin
    return payload
