from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from ...api import deps
from ...core.security import get_password_hash, verify_password
from ...db import models
from ...services.progress_service import recommend_course_slug

router = APIRouter(prefix="/api/users", tags=["users"])


def _serialize_user_profile(
    user: models.User,
    *,
    recommended_course: str | None = None,
    completed_lessons: int | None = None,
) -> dict:
    display_name = getattr(user, "full_name", None) or getattr(user, "name", None)
    return {
        "id": user.id,
        "email": user.email,
        "name": display_name,
        "full_name": display_name,
        "role": user.role,
        "level": user.level,
        "age": user.age,
        "target": user.target,
        "daily_minutes": user.daily_minutes,
        "recommended_course": recommended_course,
        "completed_lessons_count": completed_lessons,
    }


@router.get("")
def list_users(request: Request, db: Session = Depends(deps.current_db)):
    deps.require_admin(request, db=db)
    users = db.query(models.User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "level": u.level,
            "age": u.age,
            "target": u.target,
            "name": getattr(u, "full_name", None),
        }
        for u in users
    ]


@router.get("/{user_id}")
def get_user(user_id: int, request: Request, db: Session = Depends(deps.current_db)):
    deps.require_admin(request, db=db)
    user = db.get(models.User, user_id)
    if not user:
        return {"detail": "Not found"}
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "level": user.level,
        "age": user.age,
        "target": user.target,
        "name": getattr(user, "full_name", None),
    }


@router.get("/me")
def users_me(request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    completed_lessons = (
        db.query(models.UserLessonProgress)
        .filter(models.UserLessonProgress.user_id == user.id, models.UserLessonProgress.status == "finished")
        .count()
    )
    recommended_course = recommend_course_slug(user.age, user.target, getattr(user, "level", None))
    return _serialize_user_profile(
        user,
        recommended_course=recommended_course,
        completed_lessons=completed_lessons,
    )


@router.put("/me")
def update_me(payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    errors: list[str] = []

    name_raw = payload.get("name") or payload.get("full_name")
    email_raw = payload.get("email")
    current_password = payload.get("current_password") or payload.get("password_current")
    new_password = payload.get("new_password") or payload.get("password")
    confirm_password = payload.get("confirm_password")

    if name_raw is not None:
        cleaned_name = str(name_raw).strip()
        if len(cleaned_name) < 2:
            errors.append("Имя должно содержать минимум 2 символа.")
        else:
            user.full_name = cleaned_name

    if email_raw is not None:
        cleaned_email = str(email_raw).strip()
        normalized_current = (user.email or "").strip().lower()
        # If user didn't really change email (or only changed casing/whitespace), skip validation.
        if cleaned_email and cleaned_email.lower() != normalized_current:
            try:
                normalized_email = str(EmailStr(cleaned_email)).lower()
            except Exception:
                errors.append("Введите корректный email.")
            else:
                conflict = db.query(models.User).filter(models.User.email == normalized_email).first()
                if conflict and conflict.id != user.id:
                    errors.append("Такой email уже используется.")
                else:
                    user.email = normalized_email
        elif cleaned_email and cleaned_email.lower() == normalized_current:
            # Keep existing email as-is
            pass
        elif cleaned_email == "":
            # Ignore empty email updates; do not overwrite existing email
            pass

    password_errors: list[str] = []
    new_hashed_password: str | None = None
    if new_password is not None:
        new_password = str(new_password)
        if len(new_password.strip()) < 6:
            password_errors.append("Пароль должен содержать не менее 6 символов.")
        if not current_password:
            password_errors.append("Введите текущий пароль.")
        elif not verify_password(str(current_password), user.hashed_password):
            password_errors.append("Текущий пароль неверный.")
        if confirm_password is not None and str(confirm_password) != new_password:
            password_errors.append("Пароли не совпадают.")
        if not password_errors:
            new_hashed_password = get_password_hash(new_password)

    errors.extend(password_errors)

    for field in ("photo_url", "language"):
        if field in payload and payload[field] is not None:
            setattr(user, field, payload[field])

    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors if len(errors) > 1 else errors[0],
        )

    if new_hashed_password:
        user.hashed_password = new_hashed_password

    db.add(user)
    db.commit()
    db.refresh(user)
    recommended_course = recommend_course_slug(user.age, user.target, getattr(user, "level", None))
    return _serialize_user_profile(user, recommended_course=recommended_course)
