from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..dependencies import get_current_user
from ..services import recommend_course_slug
from ..services.progress import get_progress_for_user
from ..templating import render_template

router = APIRouter(tags=["courses"])


@router.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    courses = db.query(models.Course).options(selectinload(models.Course.modules)).all()
    recommended_slug = request.session.get("course_slug") or recommend_course_slug(
        request.session.get("age"), request.session.get("target")
    )
    recommended = next((c for c in courses if c.slug == recommended_slug), courses[0] if courses else None)
    current_user = getattr(request.state, "user", None)
    progress = (
        get_progress_for_user(db, current_user.id, recommended.slug if recommended else None)
        if current_user
        else {}
    )
    return render_template(
        request,
        "index.html",
        {
            "courses": courses,
            "recommended": recommended,
            "home_progress": progress,
        },
    )


@router.get("/courses")
async def courses_page(request: Request, db: Session = Depends(get_db)):
    courses = db.query(models.Course).options(selectinload(models.Course.modules).selectinload(models.Module.lessons)).all()
    current_user = getattr(request.state, "user", None)
    course_progress = {}
    if current_user:
        for c in courses:
            percent, next_lesson, _ = _calculate_progress(db, current_user, c)
            course_progress[c.id] = {"percent": percent, "next_lesson": next_lesson}
    return render_template(
        request,
        "courses.html",
        {
            "courses": courses,
            "course_progress": course_progress,
        },
    )


def _calculate_progress(db: Session, user: Optional[models.User], course: models.Course):
    lesson_ids = [lesson.id for module in course.modules for lesson in module.lessons]
    if not lesson_ids:
        return 0, None, {}
    progress_rows = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == (user.id if user else None), models.UserProgress.lesson_id.in_(lesson_ids))
        .all()
        if user
        else []
    )
    progress_map = {row.lesson_id: row.status for row in progress_rows}
    completed = sum(1 for lid in lesson_ids if progress_map.get(lid) == "done")
    progress_percent = int((completed / len(lesson_ids)) * 100) if lesson_ids else 0

    next_lesson = None
    for module in course.modules:
        for lesson in module.lessons:
            if progress_map.get(lesson.id) != "done":
                next_lesson = lesson
                break
        if next_lesson:
            break
    if not next_lesson and course.modules and course.modules[0].lessons:
        next_lesson = course.modules[0].lessons[0]
    return progress_percent, next_lesson, progress_map


@router.get("/course/{slug}")
async def course_page(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    course = (
        db.query(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
        .filter(models.Course.slug == slug)
        .first()
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    progress_percent, next_lesson, progress_map = _calculate_progress(db, user, course)

    return render_template(
        request,
        "course_page.html",
        {
            "course": course,
            "progress": progress_percent,
            "next_lesson": next_lesson,
            "progress_map": progress_map,
        },
    )
