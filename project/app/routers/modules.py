from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..dependencies import get_current_user
from ..templating import render_template

router = APIRouter(tags=["modules"])


@router.get("/course/{slug}/module/{module_id}")
async def module_page(
    slug: str,
    module_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    module = (
        db.query(models.Module)
        .options(selectinload(models.Module.lessons))
        .filter(models.Module.id == module_id)
        .first()
    )
    course = db.query(models.Course).filter_by(slug=slug).first()
    if not module or not course or module.course_id != course.id:
        raise HTTPException(status_code=404, detail="Module not found")

    progress_map = {}
    lesson_ids = [lesson.id for lesson in module.lessons]
    if lesson_ids:
        rows = (
            db.query(models.UserProgress)
            .filter(models.UserProgress.user_id == user.id, models.UserProgress.lesson_id.in_(lesson_ids))
            .all()
        )
        progress_map = {row.lesson_id: row.status for row in rows}

    return render_template(request, "module_page.html", {"module": module, "course": course, "progress_map": progress_map})
