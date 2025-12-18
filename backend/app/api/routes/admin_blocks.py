from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session, selectinload

from ...api import deps
from ...db import models
from ...schemas.block import LessonBlockUpdate, validate_block_payload
from ...services.progress_service import normalize_block, ordered_blocks

router = APIRouter(prefix="/api/admin/blocks", tags=["admin-blocks"])


def _normalize_orders(db: Session, lesson: models.Lesson) -> None:
    blocks = ordered_blocks(lesson)
    lesson.blocks_order = [b.id for b in blocks]
    for idx, block in enumerate(blocks, start=1):
        if block.order != idx:
            block.order = idx
            db.add(block)
    db.add(lesson)
    db.commit()


def _get_block(block_id: int, db: Session) -> models.LessonBlock:
    block = (
        db.query(models.LessonBlock)
        .options(selectinload(models.LessonBlock.lesson).selectinload(models.Lesson.blocks))
        .filter(models.LessonBlock.id == block_id, models.LessonBlock.is_deleted.is_(False))
        .first()
    )
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")
    return block


def _sync_special_block(block: models.LessonBlock, content: dict, db: Session) -> None:
    # Pronunciation is derived from flashcards; do not touch missing tables.
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


@router.put("/{block_id}")
def update_block(block_id: int, payload: LessonBlockUpdate, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    block = _get_block(block_id, db)
    lesson = block.lesson
    next_type = payload.type or block.block_type
    normalized_type = "audio_task" if next_type == "audio-task" else next_type
    if normalized_type not in models.BLOCK_TYPE_CHOICES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported block type")

    if payload.content is not None:
        try:
            cleaned = validate_block_payload(normalized_type, payload.content)
        except ValidationError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"error": "Invalid block content", "details": exc.errors()})
        block.content = cleaned
        block.data = cleaned
    if payload.type:
        block.block_type = normalized_type

    if payload.order is not None:
        blocks = ordered_blocks(lesson)
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
        lesson.blocks_order = [b.id for b in sorted(blocks, key=lambda i: i.order if hasattr(i, "order") else 0)]

    db.add(block)
    db.add(lesson)
    db.commit()
    db.refresh(block)
    _sync_special_block(block, block.data or block.content or {}, db)
    _normalize_orders(db, lesson)
    return normalize_block(block, lesson)


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(block_id: int, db: Session = Depends(deps.current_db), user=Depends(deps.require_admin)):
    block = _get_block(block_id, db)
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
