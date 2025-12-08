from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import UserOut
from ..dependencies import get_current_user
from ..services.dictionary import (
    bump_word_of_week_view,
    ensure_word_of_week,
    get_stats,
    get_user_dictionary_grouped,
)
from ..services.progress import get_progress_for_user
from ..templating import render_template

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=UserOut)
async def read_current_user(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, redirect_on_fail=False)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    db_user = db.get(models.User, user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(UserOut.from_orm(db_user).dict())


@router.get("/profile")
async def profile_page(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    selected_slug = request.session.get("course_slug")
    progress = get_progress_for_user(db, user.id, selected_slug)
    course = db.get(models.Course, progress.get("course_id")) if progress.get("course_id") else None
    grouped_dict = get_user_dictionary_grouped(user.id, db)
    vocab_stats = get_stats(user.id, db)
    word_of_week = ensure_word_of_week(db)
    if word_of_week:
        bump_word_of_week_view(word_of_week, db)
    return render_template(
        request,
        "profile.html",
        {
            "user": user,
            "course": course,
            "progress": progress,
            "certificates": progress.get("certificates", []),
            "modules_list": progress.get("completed_module_names", []),
            "lessons_list": progress.get("completed_lesson_titles", []),
            "dictionary_groups": grouped_dict,
            "vocab_stats": vocab_stats,
            "word_of_week": word_of_week,
        },
    )


@router.get("/dashboard")
async def dashboard_redirect():
    return RedirectResponse("/profile", status_code=status.HTTP_302_FOUND)


@router.get("/settings")
async def settings_page(request: Request, user: models.User = Depends(get_current_user)):
    return render_template(request, "settings.html", {"user": user})


@router.get("/progress")
async def progress_page(request: Request, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    selected_slug = request.session.get("course_slug")
    progress = get_progress_for_user(db, user.id, selected_slug)
    course = db.get(models.Course, progress.get("course_id")) if progress.get("course_id") else None
    return render_template(
        request,
        "dashboard.html",
        {
            "user": user,
            "course": course,
            "progress": progress.get("percent", 0),
            "completed": progress.get("completed_lessons", 0),
            "total": progress.get("total_lessons", 0),
            "remaining": max(0, progress.get("total_lessons", 0) - progress.get("completed_lessons", 0)),
            "hours": 0,
            "next_lesson": None,
        },
    )
