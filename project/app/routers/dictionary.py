import hashlib
import random
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from gtts import gTTS
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..dependencies import get_current_user
from ..services.dictionary import (
    add_word_to_dictionary,
    bump_word_of_week_correct,
    bump_word_of_week_view,
    ensure_word_of_week,
    get_neighbor_word,
    get_stats,
    get_user_dictionary_grouped,
    get_user_vocabulary,
    mark_word_learned,
    pick_training_word,
    process_game_result,
)
from ..templating import render_template

router = APIRouter(tags=["dictionary"])

AUDIO_DIR = Path(__file__).resolve().parents[1] / "static" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def _serialize_word(word: models.VocabularyWord | None) -> dict:
    if not word:
        return {}
    return {
        "id": word.id,
        "word": word.word,
        "translation": word.translation,
        "definition": word.definition or "",
        "example": word.example_sentence or "",
        "audio_url": word.audio_url or "",
        "image_url": word.image_url or "",
        "course_id": word.course_id,
        "learned": bool(word.learned),
    }


def _bump_week_if_match(word: models.VocabularyWord, db: Session) -> None:
    today = date.today()
    entry = (
        db.query(models.WordOfTheWeek)
        .filter(
            models.WordOfTheWeek.word_id == word.id,
            models.WordOfTheWeek.start_date <= today,
            models.WordOfTheWeek.end_date >= today,
        )
        .first()
    )
    if entry:
        bump_word_of_week_correct(entry, db)


@router.get("/dictionary")
async def legacy_dictionary_redirect(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # serve the same page to keep backward compatibility with the prompt
    return await vocabulary_page(request, db, user)  # type: ignore[arg-type]


@router.get("/vocabulary")
async def vocabulary_page(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    words = get_user_vocabulary(user.id, db)
    grouped = get_user_dictionary_grouped(user.id, db)
    initial_word = words[0] if words else None
    word_of_week = ensure_word_of_week(db)
    if word_of_week:
        bump_word_of_week_view(word_of_week, db)
    return render_template(
        request,
        "dictionary.html",
        {
            "words": words,
            "initial_word": initial_word,
            "grouped": grouped,
            "word_of_week": word_of_week,
            "user": user,
        },
    )


@router.get("/vocabulary/next")
async def vocabulary_next(
    id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    word = get_neighbor_word(user.id, id, "next", db)
    return JSONResponse(_serialize_word(word))


@router.get("/vocabulary/prev")
async def vocabulary_prev(
    id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    word = get_neighbor_word(user.id, id, "prev", db)
    return JSONResponse(_serialize_word(word))


@router.post("/vocabulary/learn/{word_id}")
async def vocabulary_learn(
    word_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    success = mark_word_learned(word_id, user.id, db)
    return JSONResponse({"success": success})


@router.post("/vocabulary/add/{word_id}")
async def vocabulary_add_from_other(
    word_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    source = db.get(models.VocabularyWord, word_id)
    if not source:
        raise HTTPException(status_code=404, detail="Word not found")
    entry = add_word_to_dictionary(
        user.id,
        source.course_id,
        {
            "word": source.word,
            "translation": source.translation,
            "definition": source.definition,
            "example_sentence": source.example_sentence,
            "image_url": source.image_url,
            "audio_url": source.audio_url,
        },
        db,
    )
    if "text/html" in (request.headers.get("accept") or ""):
        return RedirectResponse("/vocabulary", status_code=status.HTTP_303_SEE_OTHER)
    return JSONResponse({"added": bool(entry), "id": entry.id if entry else None})


@router.post("/dictionary/add/{word_id}")
async def dictionary_add_from_other(
    word_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return await vocabulary_add_from_other(word_id, request, db, user)  # type: ignore[arg-type]


@router.get("/vocabulary/stats")
async def vocabulary_stats(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return JSONResponse(get_stats(user.id, db))


@router.get("/dictionary/weekly")
async def vocabulary_weekly(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    wow = ensure_word_of_week(db)
    if wow:
        bump_word_of_week_view(wow, db)
    return JSONResponse({"word": _serialize_word(wow.word) if wow and wow.word else {}})


@router.get("/tts")
async def text_to_speech(
    word: str = Query(""),
    word_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    cleaned = (word or "").strip()
    if not cleaned and word_id:
        entry = db.get(models.VocabularyWord, word_id)
        cleaned = entry.word if entry else ""
    if not cleaned:
        raise HTTPException(status_code=400, detail="Укажите слово для озвучки.")

    safe_name = hashlib.md5(f"{user.id}:{cleaned}".encode()).hexdigest()
    filename = f"{safe_name}.mp3"
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        try:
            tts = gTTS(text=cleaned, lang="kk")
            tts.save(filepath)
        except Exception as exc:  # pragma: no cover - external IO
            raise HTTPException(status_code=502, detail=f"Не удалось сгенерировать аудио: {exc}") from exc

    audio_url = f"/static/audio/{filename}"
    entry = (
        db.query(models.VocabularyWord)
        .filter(models.VocabularyWord.user_id == user.id, func.lower(models.VocabularyWord.word) == cleaned.lower())
        .first()
    )
    if entry:
        entry.audio_url = audio_url
        db.add(entry)
        db.commit()
    return JSONResponse({"url": audio_url})


@router.get("/vocabulary/game/repeat")
async def vocabulary_game_repeat(
    request: Request,
    word_id: Optional[int] = Query(None),
    format: str = Query("html"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    word = pick_training_word(user.id, db, explicit_id=word_id)
    if format == "json" or request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({"word": _serialize_word(word)})
    return render_template(
        request,
        "vocabulary_game.html",
        {"mode": "repeat", "word": word, "options": [], "user": user},
    )


@router.post("/vocabulary/game/repeat/check")
async def vocabulary_game_repeat_check(
    word_id: int = Form(...),
    answer: str = Form(""),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    word = (
        db.query(models.VocabularyWord)
        .filter(models.VocabularyWord.id == word_id, models.VocabularyWord.user_id == user.id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=404, detail="Слово не найдено")

    normalized = (answer or "").strip().lower()
    correct = normalized == (word.word or "").strip().lower()
    updated = process_game_result(word, "repeat", correct, db)
    hint = f"Подсказка: {word.word[:2]}..." if not correct else ""
    if updated.learned:
        mark_word_learned(updated.id, user.id, db)
    if correct:
        _bump_week_if_match(updated, db)
    return JSONResponse(
        {
            "correct": correct,
            "hint": hint,
            "streak": updated.repeat_streak,
            "learned": updated.learned,
            "correct_answer": word.word,
        }
    )


def _mc_options(word: models.VocabularyWord, db: Session) -> list[str]:
    options = {word.translation}
    distractors = (
        db.query(models.VocabularyWord.translation)
        .filter(models.VocabularyWord.translation != word.translation)
        .order_by(func.random())
        .limit(6)
        .all()
    )
    for row in distractors:
        if len(options) >= 4:
            break
        candidate = row[0]
        if candidate:
            options.add(candidate)
    if len(options) < 4:
        extras = (
            db.query(models.Flashcard.back)
            .filter(models.Flashcard.back != word.translation)
            .order_by(func.random())
            .limit(6)
            .all()
        )
        for row in extras:
            if len(options) >= 4:
                break
            if row[0]:
                options.add(row[0])
    while len(options) < 4:
        options.add(f"{word.translation} ({len(options)})")
    options_list = list(options)
    random.shuffle(options_list)
    return options_list


@router.get("/vocabulary/game/mc")
async def vocabulary_game_mc(
    request: Request,
    word_id: Optional[int] = Query(None),
    format: str = Query("html"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    word = pick_training_word(user.id, db, explicit_id=word_id)
    options = _mc_options(word, db) if word else []
    if format == "json" or request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({"word": _serialize_word(word), "options": options})
    return render_template(
        request,
        "vocabulary_game.html",
        {"mode": "mc", "word": word, "options": options, "user": user},
    )


@router.post("/vocabulary/game/mc/check")
async def vocabulary_game_mc_check(
    word_id: int = Form(...),
    selected: str = Form(""),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    word = (
        db.query(models.VocabularyWord)
        .filter(models.VocabularyWord.id == word_id, models.VocabularyWord.user_id == user.id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=404, detail="Слово не найдено")

    correct = (selected or "").strip() == (word.translation or "").strip()
    updated = process_game_result(word, "mc", correct, db)
    if updated.learned:
        mark_word_learned(updated.id, user.id, db)
    if correct:
        _bump_week_if_match(updated, db)
    return JSONResponse(
        {
            "correct": correct,
            "streak": updated.mc_streak,
            "learned": updated.learned,
            "correct_answer": word.translation,
        }
    )


@router.get("/vocabulary/game/write")
async def vocabulary_game_write(
    request: Request,
    word_id: Optional[int] = Query(None),
    format: str = Query("html"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    word = pick_training_word(user.id, db, explicit_id=word_id)
    if format == "json" or request.headers.get("accept", "").startswith("application/json"):
        return JSONResponse({"word": _serialize_word(word)})
    return render_template(
        request,
        "vocabulary_game.html",
        {"mode": "write", "word": word, "options": [], "user": user},
    )


@router.post("/vocabulary/game/write/check")
async def vocabulary_game_write_check(
    word_id: int = Form(...),
    answer: str = Form(""),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    word = (
        db.query(models.VocabularyWord)
        .filter(models.VocabularyWord.id == word_id, models.VocabularyWord.user_id == user.id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=404, detail="Слово не найдено")

    normalized = (answer or "").strip().lower()
    correct = normalized == (word.translation or "").strip().lower()
    updated = process_game_result(word, "write", correct, db)
    hint = word.example_sentence or ""
    if updated.learned:
        mark_word_learned(updated.id, user.id, db)
    if correct:
        _bump_week_if_match(updated, db)
    return JSONResponse(
        {
            "correct": correct,
            "streak": updated.write_streak,
            "learned": updated.learned,
            "hint": hint,
            "correct_answer": word.translation,
        }
    )
