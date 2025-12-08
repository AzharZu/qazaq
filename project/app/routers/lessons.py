from datetime import datetime
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, selectinload

from .. import models
from ..database import get_db
from ..dependencies import get_current_user, require_user
from ..services.dictionary import add_flashcards_to_dictionary
from ..templating import render_template

router = APIRouter(tags=["lessons"])


@router.get("/lesson/{lesson_id}")
async def lesson_page(
    lesson_id: int,
    request: Request,
    db: Session = Depends(get_db),
    view: str = Query("theory"),
    word_index: int = Query(0),
    user: models.User = Depends(get_current_user),
):
    lesson = (
        db.query(models.Lesson)
        .options(
            selectinload(models.Lesson.blocks),
            selectinload(models.Lesson.flashcards),
            selectinload(models.Lesson.quizzes),
            selectinload(models.Lesson.module)
            .selectinload(models.Module.course)
            .selectinload(models.Course.modules)
            .selectinload(models.Module.lessons),
            selectinload(models.Lesson.module).selectinload(models.Module.lessons),
        )
        .filter(models.Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    progress_map = {}
    progress = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == user.id, models.UserProgress.lesson_id == lesson.id)
        .first()
    )
    if not progress:
        progress = models.UserProgress(user_id=user.id, lesson_id=lesson.id, status="in_progress")
        db.add(progress)
        db.commit()
    progress_status = progress.status

    course = (
        db.query(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
        .filter(models.Course.id == lesson.module.course.id)
        .first()
    )
    course = course or lesson.module.course

    lesson_ids = [l.id for m in course.modules for l in m.lessons] if course.modules else []
    if lesson_ids:
        rows = (
            db.query(models.UserProgress)
            .filter(models.UserProgress.user_id == user.id, models.UserProgress.lesson_id.in_(lesson_ids))
            .all()
        )
        progress_map = {row.lesson_id: row.status for row in rows}

    completed = sum(1 for lid in lesson_ids if progress_map.get(lid) == "done") if lesson_ids else 0
    course_progress = int((completed / len(lesson_ids)) * 100) if lesson_ids else 0

    module_lessons = lesson.module.lessons
    module_completed = sum(1 for l in module_lessons if progress_map.get(l.id) == "done") if module_lessons else 0
    module_progress = int((module_completed / len(module_lessons)) * 100) if module_lessons else 0
    lesson_progress_value = 100 if progress_status == "done" else 50 if progress_status == "in_progress" else 0

    template_name = {
        "theory": "lesson_page_theory.html",
        "flashcards": "lesson_page_flashcards.html",
        "tasks": "lesson_page_tasks.html",
        "words": "lesson_word_practice.html",
    }.get(view, "lesson_page_theory.html")

    word_list = lesson.flashcards or []
    safe_index = max(0, min(word_index, len(word_list) - 1)) if word_list else 0
    selected_word = word_list[safe_index] if word_list else None
    word_progress = int(((safe_index) / len(word_list)) * 100) if word_list else 0

    response = render_template(
        request,
        template_name,
        {
            "lesson": lesson,
            "progress_status": progress_status,
            "course_progress": course_progress,
            "module_progress": module_progress,
            "lesson_progress": lesson_progress_value,
            "progress_map": progress_map,
            "word": selected_word,
            "word_index": safe_index,
            "word_total": len(word_list),
            "word_progress": word_progress,
        },
    )
    # add flashcards to dictionary if authenticated
    try:
        add_flashcards_to_dictionary(user.id, lesson.module.course.id, lesson.flashcards, db)
    except Exception:
        pass
    return response


@router.post("/lesson/{lesson_id}/complete")
async def complete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_user),
):
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    entry = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == user.id, models.UserProgress.lesson_id == lesson_id)
        .first()
    )
    now = datetime.utcnow()
    if not entry:
        entry = models.UserProgress(
            user_id=user.id,
            lesson_id=lesson_id,
            status="done",
            completed_at=now,
            last_opened_at=now,
        )
        db.add(entry)
    else:
        entry.status = "done"
        entry.completed_at = now
        db.add(entry)

    db.commit()

    # decide next step: go to next lesson in same module if exists, else course page
    lesson = db.query(models.Lesson).options(selectinload(models.Lesson.module).selectinload(models.Module.lessons)).get(lesson_id)
    redirect_url = f"/lesson/{lesson_id}"
    if lesson and lesson.module and lesson.module.lessons:
        ordered_lessons = sorted(lesson.module.lessons, key=lambda l: l.order)
        current_index = next((idx for idx, l in enumerate(ordered_lessons) if l.id == lesson_id), None)
        if current_index is not None and current_index + 1 < len(ordered_lessons):
            next_lesson = ordered_lessons[current_index + 1]
            redirect_url = f"/lesson/{next_lesson.id}"
        elif lesson.module.course:
            redirect_url = f"/course/{lesson.module.course.slug}"

    return RedirectResponse(redirect_url, status_code=302)


@router.post("/lesson/{lesson_id}/word-progress")
async def save_word_progress(
    lesson_id: int,
    request: Request,
    word_index: int = Form(...),
    status: str = Form("in_progress"),
    user: models.User = Depends(require_user),
    db: Session = Depends(get_db),
):
    # basic session-level tracking to avoid schema changes
    key = "word_progress"
    data = request.session.get(key) or {}
    data[str(lesson_id)] = {"word_index": word_index, "status": status, "user_id": user.id}
    request.session[key] = data
    return {"ok": True}
