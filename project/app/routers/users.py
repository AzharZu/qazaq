from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import UserOut
from ..dependencies import get_current_user
from ..services.dictionary import get_user_dictionary_grouped
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
    progress = get_progress_for_user(db, user.id)
    course = (
        db.query(models.Course)
        .filter(models.Course.name == progress["course_title"])
        .first()
        if progress.get("course_title")
        else None
    )
    grouped_dict = get_user_dictionary_grouped(user.id, db)
    return render_template(
        request,
        "profile.html",
        {
            "user": user,
            "course": course,
            "progress": progress,
            "certificates": progress.get("certificates", []),
            "modules_list": [m.name if hasattr(m, 'name') else m.get("title") for m in progress.get("completed_modules", [])],
            "dictionary_groups": grouped_dict,
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
    progress = get_progress_for_user(db, user.id)
    course = (
        db.query(models.Course)
        .filter(models.Course.name == progress["course_title"])
        .first()
        if progress.get("course_title")
        else None
    )
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
