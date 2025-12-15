from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ...api import deps
from ...db import models

router = APIRouter(prefix="/api/audio-task", tags=["audio-task"])


def _get_audio_block(block_id: int, db: Session) -> models.LessonBlock:
    block = db.get(models.LessonBlock, block_id)
    if not block or getattr(block, "is_deleted", False) or block.block_type not in {"audio_task", "audio-task"}:
        raise HTTPException(status_code=404, detail="Audio task not found")
    return block


@router.post("/submit")
def submit_audio_task(payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    block_id = payload.get("block_id")
    answer_text = (payload.get("answer") or payload.get("answer_text") or "").strip()
    selected_option = payload.get("selected_option")
    if not block_id:
        raise HTTPException(status_code=400, detail="block_id is required")
    block = _get_audio_block(int(block_id), db)
    lesson_id = block.lesson_id
    data = block.data or block.content or {}
    options = data.get("options") or []
    correct_answer = (data.get("correct_answer") or "").strip()
    answer_type = data.get("answer_type") or ("multiple_choice" if options else "text")

    user_answer = answer_text
    if selected_option is not None and options:
        try:
            user_answer = options[int(selected_option)]
        except Exception:
            user_answer = answer_text or ""

    correct = user_answer.strip().lower() == correct_answer.strip().lower()
    feedback = data.get("feedback") or ("Верно" if correct else "Попробуйте ещё")

    # persist attempt in LessonProgress
    lp = (
        db.query(models.LessonProgress)
        .filter(models.LessonProgress.user_id == user.id, models.LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not lp:
        lp = models.LessonProgress(user_id=user.id, lesson_id=lesson_id, completed=False, time_spent=0, details={})
    details = lp.details or {}
    attempts = details.get("audio_tasks") or []
    attempts.append(
        {
          "block_id": block_id,
          "answer": user_answer,
          "correct": correct,
          "submitted_at": datetime.utcnow().isoformat(),
        }
    )
    details["audio_tasks"] = attempts[-100:]
    lp.details = details
    db.add(lp)
    db.commit()

    return {
        "correct": correct,
        "feedback": feedback,
        "expected": correct_answer if not correct else None,
    }
