from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...api import deps
from ...db import models
from ...services.pronunciation_service import score_to_status
from ...services import vocabulary_service

router = APIRouter(prefix="/api/dictionary", tags=["dictionary"])


@router.get("")
def get_dictionary(request: Request, lessonId: int | None = None, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    words = vocabulary_service.fetch_user_dictionary(user.id, db, lesson_id=lessonId)
    word_ids = [w.id for w in words]
    progress_entries = []
    if word_ids:
        progress_entries = (
            db.query(models.PronunciationResult)
            .filter(models.PronunciationResult.word_id.in_(word_ids), models.PronunciationResult.user_id == user.id)
            .all()
        )
    progress_map: dict[int, dict] = {}
    for entry in progress_entries:
        stats = progress_map.setdefault(entry.word_id, {"success": 0, "fails": 0, "last_review": None})
        status_label = score_to_status(entry.score)
        if status_label in {"excellent", "good", "ok"}:
            stats["success"] += 1
        else:
            stats["fails"] += 1
        stats["last_review"] = entry.created_at.isoformat() if entry.created_at else stats.get("last_review")

    def _status(word: models.VocabularyWord) -> str:
        return vocabulary_service.derive_status(word, progress_map.get(word.id, {"success": 0, "fails": 0}))

    sorted_words = sorted(
        words,
        key=lambda w: (
            {"new": 0, "learning": 1, "learned": 2}.get(_status(w), 1),
            -(w.id or 0),
        ),
    )

    unique_sorted: list[models.VocabularyWord] = []
    seen_ids: set[int] = set()
    for w in sorted_words:
        if w.id in seen_ids:
            continue
        seen_ids.add(w.id)
        unique_sorted.append(w)

    return [
        {
            "id": w.id,
            "word": w.word,
            "translation": w.translation,
            "audio_url": w.audio_url,
            "image_url": w.image_url,
            "example_sentence": w.example_sentence,
            "source_lesson_id": w.source_lesson_id,
            "source_block_id": w.source_block_id,
            "status": _status(w),
            "last_practiced_at": (w.last_practiced_at.isoformat() if getattr(w, "last_practiced_at", None) else None),
            "progress": progress_map.get(w.id, {"success": 0, "fails": 0, "last_review": None}),
        }
        for w in unique_sorted
    ]


@router.post("/add", status_code=status.HTTP_201_CREATED)
def add_dictionary_entry(payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    # Manual adds disabled; dictionary is derived from lessons only.
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dictionary entries are derived from lessons")


@router.post("/{word_id}/success", status_code=status.HTTP_201_CREATED)
def mark_success(word_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    word = db.get(models.VocabularyWord, word_id)
    if not word or word.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
    result = models.PronunciationResult(
        user_id=user.id,
        word_id=word_id,
        audio_url="",
        score=1.0,
    )
    db.add(result)
    db.commit()
    return {"ok": True, "status": "excellent"}


@router.post("/{word_id}/fail", status_code=status.HTTP_201_CREATED)
def mark_fail(word_id: int, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    word = db.get(models.VocabularyWord, word_id)
    if not word or word.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
    result = models.PronunciationResult(
        user_id=user.id,
        word_id=word_id,
        audio_url="",
        score=0.0,
    )
    db.add(result)
    db.commit()
    return {"ok": True, "status": "bad"}


@router.post("/{word_id}/result", status_code=status.HTTP_200_OK)
def submit_result(word_id: int, payload: dict, request: Request, db: Session = Depends(deps.current_db)):
    user = deps.require_user(request, db=db)
    mode = payload.get("mode") or "repeat"
    correct = bool(payload.get("correct"))
    if mode not in vocabulary_service.ALLOWED_MODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mode")
    word = db.get(models.VocabularyWord, word_id)
    if not word or word.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
    updated = vocabulary_service.process_game_result(word, mode, correct, db)
    status_label = vocabulary_service.derive_status(updated, {"success": updated.correct_attempts, "fails": updated.wrong_attempts})
    return {
        "id": updated.id,
        "word": updated.word,
        "translation": updated.translation,
        "status": status_label,
        "audio_url": updated.audio_url,
        "image_url": updated.image_url,
        "example_sentence": updated.example_sentence,
        "last_practiced_at": updated.last_practiced_at.isoformat() if updated.last_practiced_at else None,
        "progress": {
            "success": updated.correct_attempts or 0,
            "fails": updated.wrong_attempts or 0,
            "last_review": updated.created_at.isoformat() if updated.created_at else None,
        },
    }
