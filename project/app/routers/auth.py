from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import UserCreate
from ..services import create_user, get_user_by_email, recommend_course_slug, verify_password
from ..sessions import attach_session_cookie, clear_user_session, set_user_session
from ..templating import render_template

router = APIRouter(tags=["auth"])


@router.get("/signup")
async def signup_form(request: Request):
    return render_template(request, "auth/signup.html", {"error": None})


@router.post("/signup")
async def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(""),
    age: int = Form(18),
    target: str = Form("general"),
    daily_minutes: int = Form(20),
    db: Session = Depends(get_db),
):
    existing = get_user_by_email(db, email)
    if existing:
        return render_template(request, "auth/signup.html", {"error": "Email уже зарегистрирован"}, status_code=status.HTTP_400_BAD_REQUEST)

    user_in = UserCreate(
        email=email,
        password=password,
        age=age,
        target=target,
        daily_minutes=daily_minutes,
    )
    user = create_user(db, user_in)
    session_token = set_user_session(request, user)
    request.session["course_slug"] = recommend_course_slug(user.age, user.target)
    response = RedirectResponse("/profile", status_code=status.HTTP_302_FOUND)
    attach_session_cookie(response, session_token)
    return response


@router.get("/login")
async def login_form(request: Request):
    return render_template(request, "auth/login.html", {"error": None})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return render_template(
            request,
            "auth/login.html",
            {"error": "Неверный email или пароль"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    session_token = set_user_session(request, user)
    request.session["course_slug"] = recommend_course_slug(user.age, user.target)
    response = RedirectResponse("/profile", status_code=status.HTTP_302_FOUND)
    attach_session_cookie(response, session_token)
    return response


@router.get("/logout")
async def logout(request: Request):
    clear_user_session(request)
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session", path="/")
    return response


@router.post("/logout")
async def logout_post(request: Request):
    clear_user_session(request)
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session", path="/")
    return response
