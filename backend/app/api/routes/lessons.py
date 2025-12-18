from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from ...api import deps
from ...db import models
from ...schemas.block import validate_block_payload
from ...schemas.lesson import LessonCreate, LessonUpdate
from ...services import vocabulary_service
from ...services.progress_service import (
    _serialize_flashcard,
    _serialize_quiz,
    get_lesson_detail,
    normalize_block,
    ordered_blocks,
    serialize_lesson,
)

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


def _lesson_query(db: Session, allow_unpublished: bool = False):
    query = (
        db.query(models.Lesson)
        .options(
            selectinload(models.Lesson.blocks),
            selectinload(models.Lesson.flashcards),
            selectinload(models.Lesson.quizzes),
            selectinload(models.Lesson.module).selectinload(models.Module.lessons).selectinload(models.Lesson.module),
            selectinload(models.Lesson.module).selectinload(models.Module.course),
        )
        .filter(models.Lesson.is_deleted.is_(False))
    )
    if allow_unpublished:
        query = query.filter(models.Lesson.status != "archived")
    else:
        query = query.filter(models.Lesson.status == "published")
    return query


@router.get("")
def lessons_list(request: Request, module_id: Optional[int] = None, db: Session = Depends(deps.current_db)):
    user = deps.get_current_user(request, db=db, allow_anonymous=True)
    allow_unpublished = bool(user and getattr(user, "is_admin", False))
    query = (
        db.query(models.Lesson)
        .options(selectinload(models.Lesson.module))
        .filter(models.Lesson.is_deleted.is_(False))
        .filter(models.Lesson.status != "archived")
    )
    if module_id:
        query = query.filter(models.Lesson.module_id == module_id)
    if not allow_unpublished:
        query = query.filter(models.Lesson.status == "published")
    lessons = sorted(query.all(), key=lambda l: l.order)
    return [serialize_lesson(l) for l in lessons]


@router.get("/{lesson_id}")
def lesson_detail(lesson_id: int, request: Request, db: Session = Depends(deps.current_db)):
    preview = request.query_params.get("preview") == "1"
    user = deps.get_current_user(request, db=db, allow_anonymous=preview)
    allow_unpublished = bool(preview or (user and getattr(user, "is_admin", False)))
    new_words_added = 0

    if user:
        detail = get_lesson_detail(db, lesson_id, user, allow_unpublished=allow_unpublished)
        if not detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        lesson = detail["lesson"]
        blocks = detail["blocks"]
        navigation = detail["navigation"]
        progress_status = detail["progress_status"]
        course_progress = detail["course_progress"]
        module_progress = detail["module_progress"]
        progress_map = detail["progress_map"]
        score = detail.get("score")
        time_spent = detail.get("time_spent")
        if not preview:
            try:
                new_words_added = vocabulary_service.sync_lesson_vocabulary(user.id, lesson, blocks, db)
            except Exception:
                # Soft-fail dictionary sync to avoid blocking lesson load
                new_words_added = 0
    else:
        lesson = _lesson_query(db, allow_unpublished=allow_unpublished).filter(models.Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        blocks = []
        for block in ordered_blocks(lesson):
            norm = normalize_block(block, lesson)
            if norm:
                blocks.append(norm)
        ordered = (
            sorted(
                [l for l in lesson.module.lessons if not getattr(l, "is_deleted", False)],
                key=lambda l: l.order,
            )
            if lesson.module
            else []
        )
        idx = next((i for i, l in enumerate(ordered) if l.id == lesson.id), None)
        navigation = {
            "prev_lesson_id": ordered[idx - 1].id if idx is not None and idx > 0 else None,
            "next_lesson_id": ordered[idx + 1].id if idx is not None and idx + 1 < len(ordered) else None,
        }
        progress_status = "in_progress"
        course_progress = 0
        module_progress = 0
        progress_map = {}
        score = None
        time_spent = None
        new_words_added = 0

    return {
        "lesson": {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "status": lesson.status,
            "difficulty": lesson.difficulty,
            "estimated_time": lesson.estimated_time,
            "language": lesson.language,
            "video_type": getattr(lesson, "video_type", None),
            "video_url": getattr(lesson, "video_url", None),
            "blocks_order": lesson.blocks_order or [],
            "module": {
                "id": lesson.module.id,
                "order": lesson.module.order,
                "course": {"slug": lesson.module.course.slug},
            },
            "blocks": blocks,
            "flashcards": [_serialize_flashcard(fc) for fc in lesson.flashcards],
            "quizzes": [_serialize_quiz(qz) for qz in lesson.quizzes],
        },
        "progress_status": progress_status,
        "score": score,
        "time_spent": time_spent,
        "course_progress": course_progress,
        "module_progress": module_progress,
        "progress_map": progress_map,
        "navigation": navigation,
        "new_words_added": new_words_added,
    }


@router.get("/{lesson_id}/flashcards")
def lesson_flashcards(lesson_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    lesson = (
        db.query(models.Lesson)
        .filter(models.Lesson.id == lesson_id, models.Lesson.is_deleted.is_(False))
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    if getattr(lesson, "status", "draft") != "published" and not getattr(user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Lesson is not published")
    cards = sorted(lesson.flashcards, key=lambda c: c.order)
    return {
        "lesson_id": lesson.id,
        "flashcards": [
            {
                "id": card.id,
                "word": card.front,
                "translation": card.back,
                "example": card.back,
                "image_url": card.image_url,
                "audio_path": getattr(card, "audio_path", None),
                "audio_url": card.audio_url,
                "order": card.order,
                "front": card.front,
                "back": card.back,
            }
            for card in cards
        ],
    }


@router.get("/{lesson_id}/pronunciation")
def lesson_pronunciation(lesson_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    lesson = (
        db.query(models.Lesson)
        .filter(models.Lesson.id == lesson_id, models.Lesson.is_deleted.is_(False))
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    if getattr(lesson, "status", "draft") != "published" and not getattr(user, "is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Lesson is not published")
    cards = sorted(lesson.flashcards, key=lambda c: c.order)
    items = []
    for card in cards:
        items.append(
            {
                "id": card.id,
                "word": card.front,
                "translation": card.back,
                "example": f"{card.front} — {card.back}",
                "image_url": card.image_url,
                "audio_path": getattr(card, "audio_path", None),
                "audio_url": card.audio_url,
            }
        )
    return {"lesson_id": lesson.id, "items": items}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_lesson(payload: LessonCreate, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    module = db.get(models.Module, payload.module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    siblings = [l for l in module.lessons if not getattr(l, "is_deleted", False)]
    order = payload.order or (len(siblings) + 1)
    lesson = models.Lesson(
        module_id=payload.module_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        difficulty=payload.difficulty,
        estimated_time=payload.estimated_time,
        age_group=payload.age_group,
        language=payload.language,
        order=order,
        blocks_order=[],
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return serialize_lesson(lesson)


@router.put("/{lesson_id}")
def update_lesson_simple(
    lesson_id: int,
    payload: LessonUpdate,
    db: Session = Depends(deps.current_db),
    user=Depends(deps.require_admin),
):
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson or getattr(lesson, "is_deleted", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    for field in ("title", "description", "status", "difficulty", "estimated_time", "age_group", "language", "version", "order"):
        value = getattr(payload, field)
        if value is not None:
            setattr(lesson, field, value)
    if payload.blocks_order is not None:
        lesson.blocks_order = payload.blocks_order
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return serialize_lesson(lesson)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson_simple(lesson_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson or getattr(lesson, "is_deleted", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    lesson.is_deleted = True
    lesson.deleted_at = datetime.utcnow()
    db.add(lesson)
    db.commit()
    return None


@router.post("/{lesson_id}/complete")
def lesson_complete(
    lesson_id: int,
    request: Request,
    payload: dict | None = None,
    db: Session = Depends(deps.current_db),
):
    user = deps.require_user(request, db=db)
    payload = payload or {}
    allow_unpublished = bool(getattr(user, "is_admin", False))

    lesson = _lesson_query(db, allow_unpublished=allow_unpublished).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    if not allow_unpublished and lesson.status != "published":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Lesson is not published")

    answers = payload.get("answers") or payload.get("test_answers") or {}
    if isinstance(answers, list):
        answers = {str(i): val for i, val in enumerate(answers)}
    time_spent = int(payload.get("time_spent") or 0)
    score = payload.get("score")

    lesson_test_block = next(
        (
            b
            for b in lesson.blocks
            if b.block_type == "lesson_test" and not getattr(b, "is_deleted", False)
        ),
        None,
    )
    total_questions = 0
    passed = True
    if lesson_test_block:
        cleaned = validate_block_payload("lesson_test", lesson_test_block.content or {})
        questions = cleaned.get("questions") or []
        total_questions = len(questions)
        computed_score = 0
        for idx, question in enumerate(questions):
            correct_answer = question.get("correct_answer")
            user_answer = answers.get(str(idx)) or answers.get(idx) or answers.get(question.get("question"))
            q_type = (question.get("type") or "single").lower()
            if q_type in {"audio_repeat", "open"}:
                # Не считаем в итоговый балл, но сохраняем детали в lp.details
                continue
            if q_type == "multiple":
                correct_set = set(map(str, correct_answer if isinstance(correct_answer, list) else [correct_answer]))
                given_set = set(map(str, user_answer or []))
                if correct_set == given_set:
                    computed_score += 1
            elif q_type == "fill-in":
                expected = (
                    correct_answer[0] if isinstance(correct_answer, list) and correct_answer else correct_answer or ""
                )
                if isinstance(user_answer, str) and user_answer.strip().lower() == str(expected).strip().lower():
                    computed_score += 1
            else:
                expected = (
                    correct_answer[0] if isinstance(correct_answer, list) and correct_answer else correct_answer or ""
                )
                if user_answer is not None and str(user_answer) == str(expected):
                    computed_score += 1
        score = computed_score
        passing_score = cleaned.get("passing_score") or 0
        passed = score >= passing_score

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
            status="done" if passed else "in_progress",
            completed_at=now if passed else None,
            last_opened_at=now,
            time_spent=time_spent,
        )
    else:
        entry.status = "done" if passed else "in_progress"
        entry.completed_at = now if passed else entry.completed_at
        entry.time_spent = (entry.time_spent or 0) + time_spent
    db.add(entry)

    lp = (
        db.query(models.LessonProgress)
        .filter(models.LessonProgress.user_id == user.id, models.LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not lp:
        lp = models.LessonProgress(
            user_id=user.id,
            lesson_id=lesson_id,
            completed=passed,
            score=score,
            time_spent=time_spent,
            details={"answers": answers, "total_questions": total_questions, "passed": passed},
        )
    else:
        lp.completed = passed or lp.completed
        lp.score = score if score is not None else lp.score
        lp.time_spent = (lp.time_spent or 0) + time_spent
        lp.details = {"answers": answers, "total_questions": total_questions, "passed": passed}
    db.add(lp)
    db.commit()

    next_id = None
    if lesson.module and lesson.module.lessons:
        ordered = sorted(
            [
                l
                for l in lesson.module.lessons
                if not getattr(l, "is_deleted", False) and (allow_unpublished or l.status == "published")
            ],
            key=lambda l: l.order,
        )
        idx = next((i for i, l in enumerate(ordered) if l.id == lesson_id), None)
        if idx is not None and idx + 1 < len(ordered):
            next_id = ordered[idx + 1].id

    return {"next_lesson_id": next_id, "passed": passed, "score": score, "total_questions": total_questions}


@router.post("/{lesson_id}/progress")
def lesson_progress(
    lesson_id: int,
    request: Request,
    payload: dict | None = None,
    db: Session = Depends(deps.current_db),
):
    user = deps.require_user(request, db=db)
    payload = payload or {}
    time_spent = int(payload.get("time_spent") or 0)
    status_override = payload.get("status")
    score = payload.get("score")

    entry = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == user.id, models.UserProgress.lesson_id == lesson_id)
        .first()
    )
    now = datetime.utcnow()
    if not entry:
        entry = models.UserProgress(
            user_id=user.id, lesson_id=lesson_id, status=status_override or "in_progress", last_opened_at=now
        )
    entry.last_opened_at = now
    if time_spent:
        entry.time_spent = (entry.time_spent or 0) + time_spent
    if status_override:
        entry.status = status_override
    db.add(entry)

    lp = (
        db.query(models.LessonProgress)
        .filter(models.LessonProgress.user_id == user.id, models.LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not lp:
        lp = models.LessonProgress(
            user_id=user.id,
            lesson_id=lesson_id,
            completed=entry.status == "done",
            score=score,
            time_spent=time_spent,
        )
    else:
        lp.time_spent = (lp.time_spent or 0) + time_spent
        if score is not None:
            lp.score = score
        lp.completed = lp.completed or entry.status == "done"
    db.add(lp)

    db.commit()
    return {"ok": True, "status": entry.status, "time_spent": entry.time_spent}
