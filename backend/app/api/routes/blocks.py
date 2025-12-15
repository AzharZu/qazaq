from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...api import deps
from ...db import models
from ...services.progress_service import normalize_block, ordered_blocks

router = APIRouter(prefix="/api/blocks", tags=["blocks"])


@router.get("")
def list_blocks(lesson_id: int, db: Session = Depends(deps.current_db)):
    lesson = db.get(models.Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    blocks = []
    for block in ordered_blocks(lesson):
        norm = normalize_block(block, lesson)
        if norm:
            blocks.append(norm)
    return blocks
