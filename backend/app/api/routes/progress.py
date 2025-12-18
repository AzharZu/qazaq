from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError

from ...api import deps
from ...db import models
from ...schemas.progress import ProgressPayload
from ...services.progress_service import get_progress_for_user

router = APIRouter(prefix="/api/progress", tags=["progress"])

_progress_tables_checked = False


def _ensure_progress_tables(db: Session) -> None:
    global _progress_tables_checked
    if _progress_tables_checked:
        return
    bind = db.get_bind()
    inspector = inspect(bind)
    existing = set(inspector.get_table_names())
    tables_to_create = []
    if models.DailyGoal.__tablename__ not in existing:
        tables_to_create.append(models.DailyGoal.__table__)
    if models.UserStats.__tablename__ not in existing:
        tables_to_create.append(models.UserStats.__table__)
    for table in tables_to_create:
        table.create(bind=bind, checkfirst=True)
    _progress_tables_checked = True


@router.get("", response_model=ProgressPayload)
def user_progress(request: Request, db: Session = Depends(deps.current_db)):
    user = deps.get_user_or_none(request, db=db)
    if not user:
        return ProgressPayload(
            course_id=None,
            course_slug="",
            course_title="",
            completed_lessons=0,
            total_lessons=0,
            percent=0,
            completed_modules=[],
            completed_module_names=[],
            completed_lesson_titles=[],
            certificates=[],
            next_lesson=None,
            progress_map={},
            xp_total=0,
            xp_today=0,
            streak_days=0,
            goal_today={},
        )
    try:
        _ensure_progress_tables(db)
    except Exception:
        db.rollback()
    selected_slug = request.session.get("course_slug")
    progress = get_progress_for_user(db, user.id, selected_slug)
    try:
        stats = (
            db.query(models.UserStats)
            .filter(models.UserStats.user_id == user.id)
            .first()
            or models.UserStats(user_id=user.id, xp_total=0, xp_today=0, streak_days=0)
        )
        goal = (
            db.query(models.DailyGoal)
            .filter(models.DailyGoal.user_id == user.id)
            .order_by(models.DailyGoal.id.desc())
            .first()
            or models.DailyGoal(user_id=user.id, goal_type="light", target_value=10, completed_today=False)
        )
    except ProgrammingError:
        # If migrations were not applied yet, create the missing tables on the fly.
        db.rollback()
        _ensure_progress_tables(db)
        stats = (
            db.query(models.UserStats)
            .filter(models.UserStats.user_id == user.id)
            .first()
            or models.UserStats(user_id=user.id, xp_total=0, xp_today=0, streak_days=0)
        )
        goal = (
            db.query(models.DailyGoal)
            .filter(models.DailyGoal.user_id == user.id)
            .order_by(models.DailyGoal.id.desc())
            .first()
            or models.DailyGoal(user_id=user.id, goal_type="light", target_value=10, completed_today=False)
        )
    progress["xp_total"] = stats.xp_total or 0
    progress["xp_today"] = stats.xp_today or 0
    progress["streak_days"] = stats.streak_days or 0
    progress["goal_today"] = {
        "target": goal.target_value,
        "completed": bool(goal.completed_today),
        "goal_type": goal.goal_type,
    }
    return progress


@router.post("/lesson/{lesson_id}/start")
def lesson_progress_start(lesson_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    entry = (
        db.query(models.UserLessonProgress)
        .filter(models.UserLessonProgress.user_id == user.id, models.UserLessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not entry:
        entry = models.UserLessonProgress(user_id=user.id, lesson_id=lesson_id, status="in_progress", completed_blocks=[])
    db.add(entry)
    db.commit()
    return {"status": entry.status, "completed_blocks": entry.completed_blocks or []}


@router.post("/lesson/{lesson_id}/block-finished")
def lesson_block_finished(lesson_id: int, payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    block_idx = payload.get("block_index")
    if block_idx is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="block_index required")
    entry = (
        db.query(models.UserLessonProgress)
        .filter(models.UserLessonProgress.user_id == user.id, models.UserLessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not entry:
        entry = models.UserLessonProgress(user_id=user.id, lesson_id=lesson_id, status="in_progress", completed_blocks=[])
    blocks = entry.completed_blocks or []
    if block_idx not in blocks:
        blocks.append(block_idx)
    entry.completed_blocks = blocks
    db.add(entry)
    db.commit()
    return {"status": entry.status, "completed_blocks": blocks}


@router.post("/lesson/{lesson_id}/finish")
def lesson_progress_finish(lesson_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    entry = (
        db.query(models.UserLessonProgress)
        .filter(models.UserLessonProgress.user_id == user.id, models.UserLessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not entry:
        entry = models.UserLessonProgress(
            user_id=user.id, lesson_id=lesson_id, status="finished", completed_blocks=[]
        )
    entry.status = "finished"
    db.add(entry)
    db.commit()
    _recompute_course_progress(db, user.id, lesson_id)
    return {"status": entry.status, "completed_blocks": entry.completed_blocks or []}


@router.get("/lesson/{lesson_id}")
def lesson_progress_get(lesson_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    entry = (
        db.query(models.UserLessonProgress)
        .filter(models.UserLessonProgress.user_id == user.id, models.UserLessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not entry:
        return {"status": "not_started", "completed_blocks": []}
    return {"status": entry.status, "completed_blocks": entry.completed_blocks or []}


def _recompute_course_progress(db: Session, user_id: int, lesson_id: int):
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson or not lesson.module or not lesson.module.course:
        return
    course = lesson.module.course
    lessons = [l for m in course.modules for l in m.lessons if not getattr(l, "is_deleted", False)]
    total = len(lessons) or 1
    done = (
        db.query(models.UserLessonProgress)
        .filter(
            models.UserLessonProgress.user_id == user_id,
            models.UserLessonProgress.lesson_id.in_([l.id for l in lessons]),
            models.UserLessonProgress.status == "finished",
        )
        .count()
    )
    percent = int((done / total) * 100)
    row = (
        db.query(models.UserCourseProgress)
        .filter(models.UserCourseProgress.user_id == user_id, models.UserCourseProgress.course_id == course.id)
        .first()
    )
    if not row:
        row = models.UserCourseProgress(user_id=user_id, course_id=course.id, percent=percent)
    else:
        row.percent = percent
    db.add(row)
    db.commit()


@router.get("/course/{course_id}")
def course_progress_get(course_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    row = (
        db.query(models.UserCourseProgress)
        .filter(models.UserCourseProgress.user_id == user.id, models.UserCourseProgress.course_id == course_id)
        .first()
    )
    if row:
        return {"percent": row.percent}
    # compute on the fly
    course = db.get(models.Course, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    lessons = [l for m in course.modules for l in m.lessons if not getattr(l, "is_deleted", False)]
    total = len(lessons) or 1
    done = (
        db.query(models.UserLessonProgress)
        .filter(
            models.UserLessonProgress.user_id == user.id,
            models.UserLessonProgress.lesson_id.in_([l.id for l in lessons]),
            models.UserLessonProgress.status == "finished",
        )
        .count()
    )
    percent = int((done / total) * 100)
    return {"percent": percent}


@router.post("/flashcards")
def flashcards_progress(payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    lesson_id = payload.get("lesson_id")
    card_id = payload.get("card_id")
    correct = bool(payload.get("correct"))

    if not lesson_id or card_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lesson_id and card_id are required")

    lesson = db.get(models.Lesson, lesson_id)
    if not lesson or getattr(lesson, "is_deleted", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    # Ensure a base progress row exists for the lesson
    progress_row = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == user.id, models.UserProgress.lesson_id == lesson_id)
        .first()
    )
    now = datetime.utcnow()
    if not progress_row:
        progress_row = models.UserProgress(
            user_id=user.id,
            lesson_id=lesson_id,
            status="in_progress",
            last_opened_at=now,
            time_spent=0,
        )
    else:
        progress_row.last_opened_at = now
    db.add(progress_row)

    lp = (
        db.query(models.LessonProgress)
        .filter(models.LessonProgress.user_id == user.id, models.LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not lp:
        lp = models.LessonProgress(user_id=user.id, lesson_id=lesson_id, completed=False, time_spent=0)

    details = lp.details or {}
    flashcards = details.get("flashcards") or {}
    flashcards[str(card_id)] = {"correct": correct, "updated_at": now.isoformat()}
    summary = {
        "total": len(flashcards),
        "correct": sum(1 for v in flashcards.values() if v.get("correct")),
    }
    details["flashcards"] = flashcards
    details["flashcards_summary"] = summary
    lp.details = details
    db.add(lp)
    db.commit()

    return {"ok": True, "summary": summary}


@router.post("/block-finished")
def block_finished(payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    lesson_id = payload.get("lesson_id")
    block_id = payload.get("block_id")
    status_payload = payload.get("status") or "done"
    time_spent = payload.get("time_spent")

    if not lesson_id or not block_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="lesson_id and block_id are required")

    lesson = db.get(models.Lesson, lesson_id)
    if not lesson or getattr(lesson, "is_deleted", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    progress_row = (
        db.query(models.LessonProgress)
        .filter(models.LessonProgress.user_id == user.id, models.LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not progress_row:
        progress_row = models.LessonProgress(user_id=user.id, lesson_id=lesson_id, completed=False, time_spent=0, details={})

    details = progress_row.details or {}
    blocks = details.get("blocks") or {}
    normalized_block_id = str(block_id)
    blocks[normalized_block_id] = {
        "status": status_payload,
        "finished_at": datetime.utcnow().isoformat(),
    }
    details["blocks"] = blocks
    progress_row.details = details
    if time_spent:
        progress_row.time_spent = (progress_row.time_spent or 0) + int(time_spent)
    # Mark user_progress row as in_progress/done
    up = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == user.id, models.UserProgress.lesson_id == lesson_id)
        .first()
    )
    if not up:
        up = models.UserProgress(user_id=user.id, lesson_id=lesson_id, status="in_progress", last_opened_at=datetime.utcnow(), time_spent=0)
    else:
        up.last_opened_at = datetime.utcnow()
    lesson_block_ids = [str(b.id) for b in lesson.blocks if not getattr(b, "is_deleted", False)]
    total_unique_blocks = len(set(lesson_block_ids))
    completed_known_blocks = len({bid for bid in blocks.keys() if bid in lesson_block_ids})
    if total_unique_blocks > 0 and completed_known_blocks >= total_unique_blocks:
        up.status = "done"
        progress_row.completed = True
    db.add(progress_row)
    db.add(up)
    db.commit()
    return {"ok": True, "status": status_payload, "blocks_completed": len(blocks)}
