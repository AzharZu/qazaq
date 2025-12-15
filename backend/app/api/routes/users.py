from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ...api import deps
from ...db import models
from ...services.progress_service import recommend_course_slug

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
def list_users(request: Request, db: Session = Depends(deps.current_db)):
    deps.require_admin(request, db=db)
    users = db.query(models.User).all()
    return [
        {"id": u.id, "email": u.email, "role": u.role, "level": u.level, "age": u.age, "target": u.target}
        for u in users
    ]


@router.get("/{user_id}")
def get_user(user_id: int, request: Request, db: Session = Depends(deps.current_db)):
    deps.require_admin(request, db=db)
    user = db.get(models.User, user_id)
    if not user:
        return {"detail": "Not found"}
    return {"id": user.id, "email": user.email, "role": user.role, "level": user.level, "age": user.age, "target": user.target}


@router.get("/me")
def users_me(request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    completed_lessons = (
        db.query(models.UserLessonProgress)
        .filter(models.UserLessonProgress.user_id == user.id, models.UserLessonProgress.status == "finished")
        .count()
    )
    recommended_course = recommend_course_slug(user.age, user.target)
    return {
        "id": user.id,
        "email": user.email,
        "level": user.level,
        "recommended_course": recommended_course,
        "completed_lessons_count": completed_lessons,
    }


@router.put("/me")
def update_me(payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    for field in ("full_name", "photo_url", "language"):
        if field in payload:
            setattr(user, field, payload.get(field))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "full_name": getattr(user, "full_name", None), "photo_url": getattr(user, "photo_url", None), "language": getattr(user, "language", None)}
