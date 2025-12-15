from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...api import deps
from ...db import models
from ...services import vocabulary_service as vocab

router = APIRouter(prefix="/api/vocabulary", tags=["vocabulary"])


def _user_or_first(request: Request, db: Session) -> models.User | None:
    user = deps.get_user_or_none(request, db=db)
    if user:
        return user
    return db.query(models.User).first()


@router.get("")
def list_vocabulary(request: Request, db: Session = Depends(deps.current_db)):
    user = _user_or_first(request, db)
    if not user:
        return []
    words = vocab.get_user_vocabulary(user.id, db)
    return [vocab.serialize_word(w) for w in words]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_vocabulary(
    payload: dict,
    request: Request,
    db: Session = Depends(deps.current_db),
    user=Depends(deps.require_admin),
):
    owner = _user_or_first(request, db)
    if not owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user available")
    word = (payload.get("word") or "").strip()
    translation = (payload.get("translation") or "").strip()
    if not word or not translation:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="word and translation are required")
    entry = models.VocabularyWord(
        user_id=owner.id,
        course_id=payload.get("course_id") or 1,
        word=word,
        translation=translation,
        definition=payload.get("definition"),
        example_sentence=payload.get("example_sentence"),
        image_url=payload.get("image_url"),
        audio_url=payload.get("audio_url"),
        learned=bool(payload.get("learned", False)),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return vocab.serialize_word(entry)


@router.put("/{word_id}")
def update_vocabulary(
    word_id: int,
    payload: dict,
    request: Request,
    db: Session = Depends(deps.current_db),
    user=Depends(deps.require_admin),
):
    owner = _user_or_first(request, db)
    if not owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user available")
    entry = db.query(models.VocabularyWord).filter(models.VocabularyWord.id == word_id, models.VocabularyWord.user_id == owner.id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
    for field in ("word", "translation", "definition", "example_sentence", "image_url", "audio_url"):
        if field in payload and payload[field] is not None:
            setattr(entry, field, payload[field])
    if "learned" in payload:
        entry.learned = bool(payload["learned"])
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return vocab.serialize_word(entry)


@router.delete("/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vocabulary(
    word_id: int,
    request: Request,
    db: Session = Depends(deps.current_db),
    user=Depends(deps.require_admin),
):
    owner = _user_or_first(request, db)
    if not owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user available")
    entry = db.query(models.VocabularyWord).filter(models.VocabularyWord.id == word_id, models.VocabularyWord.user_id == owner.id).first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
    db.delete(entry)
    db.commit()
    return None


@router.get("/game")
def vocabulary_game_round(
    request: Request,
    mode: str = Query("multiple_choice"),
    word_id: Optional[int] = Query(None),
    db: Session = Depends(deps.current_db),
):
    user = _user_or_first(request, db)
    if not user:
        return {"question": None, "options": [], "correct": None, "word": {}}
    normalized_mode = "mc" if mode in {"multiple_choice", "mc"} else mode
    if normalized_mode not in vocab.ALLOWED_MODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported mode")
    word = vocab.pick_training_word(user.id, db, explicit_id=word_id)
    if not word:
        return {"question": None, "options": [], "correct": None, "word": {}}
    if normalized_mode in {"mc", "multiple_choice"}:
        mc = vocab.build_mc_question(word, db)
        mc["word"] = vocab.serialize_word(word)
        return mc
    if normalized_mode != "mc" and not word.audio_url:
        word.audio_url = ""
    options = vocab.mc_options(word, db) if normalized_mode == "write" else []
    return {"word": vocab.serialize_word(word), "options": options}


@router.post("/check")
def vocabulary_check(
    payload: dict,
    request: Request,
    db: Session = Depends(deps.current_db),
):
    user = _user_or_first(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user available")

    mode_in = payload.get("mode") or "multiple_choice"
    mode = "mc" if mode_in in {"multiple_choice", "mc"} else mode_in
    if mode not in vocab.ALLOWED_MODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported mode")

    word_id = payload.get("word_id")
    if not word_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="word_id is required")

    word = (
        db.query(models.VocabularyWord)
        .filter(models.VocabularyWord.id == word_id, models.VocabularyWord.user_id == user.id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")

    answer = (payload.get("answer") or payload.get("selected") or "").strip()
    normalized_word = (word.word or "").strip()
    normalized_translation = (word.translation or "").strip()

    correct = False
    explanation = ""
    if mode in {"mc", "multiple_choice"}:
        correct = answer.lower() == normalized_translation.lower()
    elif mode == "repeat":
        correct = answer.lower() == normalized_word.lower()
        explanation = f"Правильно: {normalized_word}"
    elif mode == "write":
        correct = answer.lower() == normalized_translation.lower()
        explanation = word.example_sentence or ""

    updated = vocab.process_game_result(word, mode, correct, db)
    if correct:
        week = vocab.ensure_word_of_week(db)
        if week and week.word_id == updated.id:
            vocab.bump_word_of_week_correct(week, db)
    if updated.learned:
        vocab.mark_word_learned(updated.id, user.id, db)

    return {
        "correct": correct,
        "explanation": explanation,
        "word_id": word.id,
    }


@router.get("/stats")
def vocabulary_stats(request: Request, db: Session = Depends(deps.current_db)):
    user = _user_or_first(request, db)
    if not user:
        return {}
    return vocab.get_stats(user.id, db)


@router.get("/weekly")
def vocabulary_word_of_week(request: Request, db: Session = Depends(deps.current_db)):
    user = _user_or_first(request, db)
    word_of_week = vocab.ensure_word_of_week(db)
    if word_of_week:
        vocab.bump_word_of_week_view(word_of_week, db)
    return {"word": vocab.serialize_word(word_of_week.word) if word_of_week and word_of_week.word else {}}


@router.get("/tts")
def text_to_speech(
    request: Request,
    word: str = Query(""),
    word_id: Optional[int] = Query(None),
    db: Session = Depends(deps.current_db),
):
    user = _user_or_first(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user available")
    cleaned = (word or "").strip()
    if not cleaned and word_id:
        entry = db.get(models.VocabularyWord, word_id)
        cleaned = entry.word if entry else ""
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Укажите слово для озвучки.")

    try:
        audio_url = vocab.tts_for_word(user.id, cleaned)
    except Exception as exc:  # pragma: no cover - external IO
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Не удалось сгенерировать аудио: {exc}") from exc

    entry = (
        db.query(models.VocabularyWord)
        .filter(models.VocabularyWord.user_id == user.id, func.lower(models.VocabularyWord.word) == cleaned.lower())
        .first()
    )
    if entry:
        entry.audio_url = audio_url
        db.add(entry)
        db.commit()
    return {"url": audio_url}


@router.get("/audio/{filename}", include_in_schema=False)
def serve_tts_audio(filename: str):
    safe_path = (vocab.AUDIO_DIR / filename).resolve()
    if vocab.AUDIO_DIR not in safe_path.parents and vocab.AUDIO_DIR != safe_path.parent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path")
    if not safe_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio not found")
    return FileResponse(safe_path, media_type="audio/mpeg")
