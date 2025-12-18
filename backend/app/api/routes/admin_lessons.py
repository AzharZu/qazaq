from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.orm import Session, selectinload
from pydantic import ValidationError

from ...api import deps
from ...db import models
from ...schemas.block import LessonBlockCreate, LessonBlockUpdate, ReorderBlocks, validate_block_payload
from ...schemas.lesson import LessonCreate, LessonUpdate
from ...services.progress_service import normalize_block, ordered_blocks, serialize_lesson

router = APIRouter(prefix="/api/admin/lessons", tags=["admin-lessons"])

# Validation codes for publish readiness
VALIDATION_ERRORS = {
    "NO_THEORY": "Theory must have text or video",
    "NO_FLASHCARDS": "At least one flashcard is required",
    "FLASHCARD_MISSING_TRANSLATION": "Every flashcard must have translation",
    "NO_TASKS": "At least one task/quiz is required",
}
VALIDATION_WARNINGS = {
    "WORDS_WITHOUT_AUDIO": "Some words lack audio",
    "WORDS_WITHOUT_IMAGE": "Some words lack image",
}

def _get_lesson(db: Session, lesson_id: int, include_deleted: bool = False) -> models.Lesson | None:
    query = (
        db.query(models.Lesson)
        .options(
            selectinload(models.Lesson.blocks),
            selectinload(models.Lesson.module).selectinload(models.Module.lessons),
        )
        .filter(models.Lesson.id == lesson_id)
    )
    if not include_deleted:
        query = query.filter(models.Lesson.is_deleted.is_(False))
    return query.first()


def _sync_special_block(block: models.LessonBlock, content: dict, db: Session) -> None:
    """Persist auxiliary tables for specialized blocks without breaking legacy fields.

    Pronunciation is derived from flashcards; no DB writes are performed here.
    """
    if block.block_type in {"audio_task", "audio-task"}:
        existing = getattr(block, "audio_task", None)
        if not existing:
            existing = models.AudioTask(block_id=block.id)
        existing.audio_path = content.get("audio_path") or content.get("audio_url")
        existing.audio_url = content.get("audio_url")
        existing.transcript = content.get("transcript")
        existing.options = content.get("options") or []
        existing.correct_answer = content.get("correct_answer")
        existing.answer_type = content.get("answer_type") or ("multiple_choice" if existing.options else "text")
        existing.feedback = content.get("feedback")
        db.add(existing)


def _normalize_orders(db: Session, lesson: models.Lesson) -> None:
    blocks = ordered_blocks(lesson)
    lesson.blocks_order = [b.id for b in blocks]
    for idx, block in enumerate(blocks, start=1):
        if block.order != idx:
            block.order = idx
            db.add(block)
    db.add(lesson)
    db.commit()


@router.get("")
def list_lessons(module_id: int | None = None, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    """Get lessons, optionally filtered by module_id."""
    query = (
        db.query(models.Lesson)
        .options(selectinload(models.Lesson.module))
        .filter(models.Lesson.is_deleted.is_(False))
    )
    if module_id is not None:
        # Validate module exists
        module = db.get(models.Module, module_id)
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        query = query.filter(models.Lesson.module_id == module_id)
    lessons = sorted(query.all(), key=lambda l: l.order)
    return [serialize_lesson(l) for l in lessons]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_lesson(payload: LessonCreate, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    module = db.get(models.Module, payload.module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    if payload.video_type and payload.video_type not in {"youtube", "vimeo", "file"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported video_type")
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
        video_type=payload.video_type or "youtube",
        video_url=payload.video_url,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return serialize_lesson(lesson) | {"blocks": []}


@router.get("/{lesson_id}")
def get_lesson(lesson_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = _get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    blocks = []
    for block in ordered_blocks(lesson):
        norm = normalize_block(block, lesson)
        if norm:
            blocks.append(norm)
    return serialize_lesson(lesson) | {
        "description": lesson.description,
        "language": lesson.language,
        "status": lesson.status,
        "difficulty": lesson.difficulty,
        "estimated_time": lesson.estimated_time,
        "blocks_order": lesson.blocks_order or [],
        "video_type": lesson.video_type,
        "video_url": lesson.video_url,
        "blocks": blocks,
    }


@router.patch("/{lesson_id}")
def update_lesson(lesson_id: int, payload: LessonUpdate, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = _get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    if payload.video_type and payload.video_type not in {"youtube", "vimeo", "file"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported video_type")

    for field in (
        "title",
        "description",
        "status",
        "difficulty",
        "estimated_time",
        "age_group",
        "language",
        "version",
        "order",
        "video_type",
        "video_url",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(lesson, field, value)

    if payload.blocks_order:
        order_map = {bid: idx + 1 for idx, bid in enumerate(payload.blocks_order)}
        for block in lesson.blocks:
            if block.id in order_map:
                block.order = order_map[block.id]
                db.add(block)
        lesson.blocks_order = payload.blocks_order

    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    _normalize_orders(db, lesson)
    blocks = []
    for block in ordered_blocks(lesson):
        norm = normalize_block(block, lesson)
        if norm:
            blocks.append(norm)
    return serialize_lesson(lesson) | {"blocks": blocks}


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(lesson_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = _get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    now = datetime.utcnow()
    lesson.is_deleted = True
    lesson.deleted_at = now
    for block in lesson.blocks:
        block.is_deleted = True
        block.deleted_at = now
        db.add(block)
    db.add(lesson)
    db.commit()
    return None


@router.post("/{lesson_id}/publish")
def publish_lesson(lesson_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = _get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    lesson.status = "published"
    lesson.version = (lesson.version or 1) + 1
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return serialize_lesson(lesson)


@router.get("/{lesson_id}/blocks")
def list_blocks(lesson_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = _get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    blocks = []
    for block in ordered_blocks(lesson):
        norm = normalize_block(block, lesson)
        if norm:
            blocks.append(norm)
    return blocks


@router.post("/{lesson_id}/blocks", status_code=status.HTTP_201_CREATED)
def create_block(lesson_id: int, payload: LessonBlockCreate, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = _get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    normalized_type = "audio_task" if payload.type == "audio-task" else payload.type
    if normalized_type not in models.BLOCK_TYPE_CHOICES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported block type")

    blocks = ordered_blocks(lesson)
    target_order = len(blocks) + 1
    if payload.insert_after:
        anchor = next((b for b in blocks if b.id == payload.insert_after), None)
        if not anchor:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="insert_after must reference an existing block")
        target_order = anchor.order + 1
        for b in blocks:
            if b.order >= target_order:
                b.order += 1
                db.add(b)

    try:
        content = validate_block_payload(normalized_type, payload.content)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "Invalid block content", "details": exc.errors()})
    block = models.LessonBlock(
        lesson_id=lesson_id,
        block_type=normalized_type,
        content=content,
        data=content,
        order=target_order,
    )
    db.add(block)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        _normalize_orders(db, lesson)
        refreshed_blocks = ordered_blocks(lesson)
        block.order = len(refreshed_blocks) + 1
        db.add(block)
        db.commit()
    db.refresh(block)
    _sync_special_block(block, content, db)
    _normalize_orders(db, lesson)
    return normalize_block(block, lesson)


@router.patch("/blocks/{block_id}")
def update_block(block_id: int, payload: LessonBlockUpdate, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    block = (
        db.query(models.LessonBlock)
        .options(selectinload(models.LessonBlock.lesson).selectinload(models.Lesson.blocks))
        .filter(models.LessonBlock.id == block_id, models.LessonBlock.is_deleted.is_(False))
        .first()
    )
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")
    lesson = block.lesson
    next_type = payload.type or block.block_type
    normalized_type = "audio_task" if next_type == "audio-task" else next_type
    if normalized_type not in models.BLOCK_TYPE_CHOICES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported block type")

    if payload.content is not None:
        try:
            block.content = validate_block_payload(normalized_type, payload.content)
            block.data = block.content
        except ValidationError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "Invalid block content", "details": exc.errors()})
    if payload.type:
        block.block_type = normalized_type

    if payload.order is not None:
        blocks = ordered_blocks(lesson)
        order_map = {bid: idx + 1 for idx, bid in enumerate(lesson.blocks_order or [])}
        desired = max(1, min(payload.order, len(blocks)))
        for b in blocks:
            if b.id == block.id:
                continue
            if desired <= b.order < block.order:
                b.order += 1
            elif block.order < b.order <= desired:
                b.order -= 1
            db.add(b)
        block.order = desired
        # Update blocks_order to match the new ordering
        ordered_ids = sorted(
            [b.id for b in blocks if b.id != block.id],
            key=lambda bid: order_map.get(bid, 0),
        )
        ordered_ids.insert(desired - 1, block.id)
        lesson.blocks_order = ordered_ids

    db.add(block)
    db.add(lesson)
    try:
        db.commit()
        db.refresh(block)
    except IntegrityError:
        db.rollback()
        _normalize_orders(db, lesson)
        db.refresh(block)
    _sync_special_block(block, block.data or block.content or {}, db)
    _normalize_orders(db, lesson)
    return normalize_block(block, lesson)


@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(block_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    block = (
        db.query(models.LessonBlock)
        .options(selectinload(models.LessonBlock.lesson).selectinload(models.Lesson.blocks))
        .filter(models.LessonBlock.id == block_id, models.LessonBlock.is_deleted.is_(False))
        .first()
    )
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")
    block.is_deleted = True
    block.deleted_at = datetime.utcnow()
    block.order = -block.id
    lesson = block.lesson
    lesson.blocks_order = [bid for bid in lesson.blocks_order or [] if bid != block.id]
    db.add(block)
    db.add(lesson)
    db.commit()
    _normalize_orders(db, lesson)
    return None


@router.get("/{lesson_id}/preview")
def preview_lesson(lesson_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = _get_lesson(db, lesson_id, include_deleted=False)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    blocks = []
    for block in ordered_blocks(lesson):
        norm = normalize_block(block, lesson)
        if norm:
            blocks.append(norm)
    return serialize_lesson(lesson) | {"blocks": blocks, "blocks_order": lesson.blocks_order or []}


@router.post("/{lesson_id}/validate")
def validate_lesson(lesson_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = _get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    blocks = ordered_blocks(lesson)
    errors: list[str] = []
    warnings: list[str] = []

    theory = next((b for b in blocks if b.block_type == "theory"), None)
    if not theory or not (theory.content.get("rich_text") or theory.content.get("markdown") or theory.content.get("video_url")):
        errors.append("NO_THEORY")

    flashcards_block = next((b for b in blocks if b.block_type == "flashcards"), None)
    cards = []
    if flashcards_block:
        cards = flashcards_block.content.get("cards") or []
    if not cards:
        errors.append("NO_FLASHCARDS")
    else:
        if any(not c.get("translation") for c in cards):
            errors.append("FLASHCARD_MISSING_TRANSLATION")
        if any(not (c.get("audio_path") or c.get("audio_url")) for c in cards):
            warnings.append("WORDS_WITHOUT_AUDIO")
        if any(not c.get("image_url") for c in cards):
            warnings.append("WORDS_WITHOUT_IMAGE")

    tasks = [b for b in blocks if b.block_type in {"quiz", "theory_quiz", "lesson_test", "audio_task"}]
    if not tasks:
        errors.append("NO_TASKS")

    return {"can_publish": len(errors) == 0, "errors": errors, "warnings": warnings}


@router.post("/blocks/{block_id}/duplicate", status_code=status.HTTP_201_CREATED)
def duplicate_block(block_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    block = (
        db.query(models.LessonBlock)
        .options(selectinload(models.LessonBlock.lesson).selectinload(models.Lesson.blocks))
        .filter(models.LessonBlock.id == block_id, models.LessonBlock.is_deleted.is_(False))
        .first()
    )
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")
    lesson = block.lesson
    duplicate = models.LessonBlock(
        lesson_id=block.lesson_id,
        block_type=block.block_type,
        content=block.content,
        order=block.order + 1,
    )
    for b in lesson.blocks:
        if b.order >= duplicate.order and not getattr(b, "is_deleted", False):
            b.order += 1
            db.add(b)
    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    _normalize_orders(db, lesson)
    return normalize_block(duplicate, lesson)


@router.post("/{lesson_id}/blocks/reorder", status_code=status.HTTP_204_NO_CONTENT)
def reorder_blocks(lesson_id: int, payload: ReorderBlocks, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    lesson = _get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    blocks = [b for b in ordered_blocks(lesson) if not getattr(b, "is_deleted", False)]
    # Canonical flow: only flashcards and task-like blocks are reorderable; fixed ones keep their place.
    reorderable = [b for b in blocks if b.block_type in {"flashcards", "audio_task", "quiz", "theory_quiz", "lesson_test", "free_writing"}]
    reorderable_ids = [b.id for b in reorderable]
    desired_ids = [bid for bid in payload.order if bid in reorderable_ids]
    if set(desired_ids) != set(reorderable_ids) or len(desired_ids) != len(reorderable_ids):
        # If payload doesn't match, keep existing order but return success to avoid frontend 409 loops.
        return None
    # Step 1: move reorderable blocks to a safe temporary range to avoid UNIQUE conflicts during swap.
    temp_base = 1000
    for idx, b in enumerate(reorderable):
        b.order = temp_base + idx
        db.add(b)
    db.flush()

    # Step 2: reassign canonical order: fixed first, then desired reorderable sequence.
    base_order = 1
    fixed = [b for b in blocks if b.id not in reorderable_ids]
    for b in fixed:
        b.order = base_order
        base_order += 1
        db.add(b)
    for bid in desired_ids:
        b = next((x for x in reorderable if x.id == bid), None)
        if b:
            b.order = base_order
            base_order += 1
            db.add(b)
    # Assign any leftover reorderable blocks that were not in desired_ids
    for b in reorderable:
        if b.id not in desired_ids:
            b.order = base_order
            base_order += 1
            db.add(b)

    lesson.blocks_order = [b.id for b in sorted(fixed + reorderable, key=lambda x: x.order)]
    db.add(lesson)
    db.commit()
    return None
