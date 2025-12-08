from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..dependencies import require_admin
from ..schemas.lesson_editor import (
    BlockCreate,
    BlockOut,
    BlockUpdate,
    LessonSummary,
    LessonUpdate,
    LessonWithBlocksOut,
    ReorderBlocks,
    validate_block_content,
)

router = APIRouter(prefix="/admin/api", tags=["lesson-editor"], dependencies=[Depends(require_admin)])


def _validate_block_type(block_type: str) -> None:
    if block_type not in models.BLOCK_TYPE_CHOICES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "unsupported_block_type", "message": f"Unsupported block type '{block_type}'"},
        )


def _get_lesson(db: Session, lesson_id: int) -> models.Lesson:
    lesson = db.execute(select(models.Lesson).where(models.Lesson.id == lesson_id)).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return lesson


def _ordered_blocks(db: Session, lesson_id: int) -> list[models.LessonBlock]:
    stmt = (
        select(models.LessonBlock)
        .where(models.LessonBlock.lesson_id == lesson_id)
        .order_by(models.LessonBlock.order, models.LessonBlock.id)
    )
    return list(db.scalars(stmt))


def _normalize_orders(db: Session, lesson_id: int) -> None:
    ordered = _ordered_blocks(db, lesson_id)
    for idx, block in enumerate(ordered, start=1):
        if block.order != idx:
            block.order = idx
            db.add(block)
    db.commit()


def _get_block(db: Session, block_id: int) -> models.LessonBlock:
    block = db.get(models.LessonBlock, block_id)
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")
    return block


@router.get("/lessons", response_model=List[LessonSummary])
def list_lessons(db: Session = Depends(get_db)):
    stmt = select(models.Lesson).order_by(models.Lesson.module_id, models.Lesson.order, models.Lesson.id)
    return list(db.scalars(stmt))


@router.get("/lessons/{lesson_id}", response_model=LessonWithBlocksOut)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = _get_lesson(db, lesson_id)
    lesson.blocks = _ordered_blocks(db, lesson_id)
    return lesson


@router.patch("/lessons/{lesson_id}", response_model=LessonWithBlocksOut)
def update_lesson(lesson_id: int, payload: LessonUpdate, db: Session = Depends(get_db)):
    lesson = _get_lesson(db, lesson_id)
    for field in ("title", "description", "status", "language", "version"):
        value = getattr(payload, field)
        if value is not None:
            setattr(lesson, field, value)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    lesson.blocks = _ordered_blocks(db, lesson_id)
    return lesson


@router.get("/lessons/{lesson_id}/blocks", response_model=list[BlockOut])
def list_blocks(lesson_id: int, db: Session = Depends(get_db)):
    _get_lesson(db, lesson_id)
    return _ordered_blocks(db, lesson_id)


@router.post("/lessons/{lesson_id}/blocks", response_model=BlockOut, status_code=status.HTTP_201_CREATED)
def create_block(lesson_id: int, payload: BlockCreate, db: Session = Depends(get_db)):
    _get_lesson(db, lesson_id)
    _validate_block_type(payload.type)
    existing = _ordered_blocks(db, lesson_id)
    target_order = len(existing) + 1
    insert_after = getattr(payload, "insert_after", None)
    if insert_after:
        anchor = next((b for b in existing if b.id == insert_after), None)
        if not anchor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "invalid_insert_after", "message": "insert_after must reference an existing block"},
            )
        target_order = anchor.order + 1

    for b in existing:
        if b.order >= target_order:
            b.order += 1
            db.add(b)

    content_dict = (
        payload.content.model_dump() if hasattr(payload.content, "model_dump") else dict(payload.content or {})
    )
    block = models.LessonBlock(
        lesson_id=lesson_id,
        block_type=payload.type,
        content=validate_block_content(payload.type, content_dict),
        order=target_order,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    _normalize_orders(db, lesson_id)
    return block


@router.patch("/blocks/{block_id}", response_model=BlockOut)
def update_block(block_id: int, payload: BlockUpdate, db: Session = Depends(get_db)):
    block = _get_block(db, block_id)
    new_type = payload.type or block.block_type
    _validate_block_type(new_type)

    if payload.content is not None:
        block.content = validate_block_content(new_type, payload.content)
    elif payload.type:
        block.content = validate_block_content(new_type, block.content)

    if payload.type:
        block.block_type = payload.type

    if payload.order is not None:
        blocks = _ordered_blocks(db, block.lesson_id)
        max_order = len(blocks)
        desired = max(1, min(payload.order, max_order))
        for b in blocks:
            if b.id == block.id:
                continue
            if desired <= b.order < block.order:
                b.order += 1
                db.add(b)
            elif block.order < b.order <= desired:
                b.order -= 1
                db.add(b)
        block.order = desired

    db.add(block)
    db.commit()
    db.refresh(block)
    _normalize_orders(db, block.lesson_id)
    return block


@router.delete("/blocks/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(block_id: int, db: Session = Depends(get_db)):
    block = _get_block(db, block_id)
    lesson_id = block.lesson_id
    db.delete(block)
    db.commit()
    _normalize_orders(db, lesson_id)
    return None


@router.post(
    "/blocks/{block_id}/duplicate",
    response_model=BlockOut,
    status_code=status.HTTP_201_CREATED,
)
def duplicate_block(block_id: int, db: Session = Depends(get_db)):
    block = _get_block(db, block_id)
    _validate_block_type(block.block_type)

    duplicate = models.LessonBlock(
        lesson_id=block.lesson_id,
        block_type=block.block_type,
        content=block.content,
        order=block.order + 1,
    )
    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    _normalize_orders(db, block.lesson_id)
    return duplicate


@router.post("/lessons/{lesson_id}/blocks/reorder", status_code=status.HTTP_204_NO_CONTENT)
def reorder_blocks(lesson_id: int, payload: ReorderBlocks, db: Session = Depends(get_db)):
    blocks = _ordered_blocks(db, lesson_id)
    current_ids = [b.id for b in blocks]
    if set(current_ids) != set(payload.order) or len(payload.order) != len(current_ids):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "order_mismatch", "message": "Order list must include every block exactly once"},
        )
    order_map = {block_id: idx + 1 for idx, block_id in enumerate(payload.order)}
    for b in blocks:
        b.order = order_map[b.id]
        db.add(b)
    db.commit()
    return None
