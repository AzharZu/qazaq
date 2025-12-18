import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from ...api import deps
from ...core.config import get_settings
from ...db import models
from ...services.pronunciation_service import evaluate_pronunciation, feedback_for_score, score_to_status

router = APIRouter(prefix="/api/pronunciation", tags=["pronunciation"])


def _resolve_expected_text(word_obj: Optional[models.VocabularyWord], payload: dict | None) -> str:
    if word_obj:
        return word_obj.word or word_obj.translation or ""
    payload = payload or {}
    items = payload.get("items") or payload.get("cards") or payload.get("words") or []
    if items:
        first = items[0] or {}
        return first.get("word") or first.get("translation") or first.get("phrase") or ""
    return (
        payload.get("expected_pronunciation")
        or payload.get("phrase")
        or payload.get("word")
        or payload.get("content")
        or ""
    )


@router.post("/check")
async def pronunciation_check(
    request: Request,
    audio: UploadFile = File(...),
    word_id: int | None = Form(None),
    target_text: str | None = Form(None),
    lesson_id: int | None = Form(None),
    block_id: int | None = Form(None),
    db: Session = Depends(deps.current_db),
):
    user = deps.require_user(request, db=db)

    word_obj = db.get(models.VocabularyWord, word_id) if word_id else None
    if word_id and (not word_obj or word_obj.user_id != user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")

    block_payload = None
    if block_id:
        block = db.get(models.LessonBlock, block_id)
        block_payload = block.data or block.content if block else None

    expected_text = target_text or _resolve_expected_text(word_obj, block_payload)
    if not expected_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="target text is required")

    data = await audio.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="audio is empty")

    settings = get_settings()
    upload_root = Path(settings.upload_root or "uploads")
    target_dir = upload_root / "pronunciation"
    target_dir.mkdir(parents=True, exist_ok=True)
    ext = ".wav"
    if audio.filename and "." in audio.filename:
        ext = f".{audio.filename.split('.')[-1]}"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = target_dir / filename
    file_path.write_bytes(data)
    audio_url = f"{settings.cdn_base_url}/pronunciation/{filename}"

    score = await evaluate_pronunciation(str(file_path), expected_text)
    status_label = score_to_status(score)
    feedback = feedback_for_score(score)

    if word_obj:
        result = models.PronunciationResult(
          user_id=user.id,
          word_id=word_obj.id,
          audio_url=audio_url,
          score=score,
        )
        db.add(result)

    # Update lesson progress if provided
    if lesson_id:
        lp = (
            db.query(models.LessonProgress)
            .filter(models.LessonProgress.user_id == user.id, models.LessonProgress.lesson_id == lesson_id)
            .first()
        )
        if not lp:
            lp = models.LessonProgress(
                user_id=user.id,
                lesson_id=lesson_id,
                completed=False,
                score=None,
                time_spent=0,
                details={},
            )
        details = lp.details or {}
        attempts = details.get("pronunciation") or []
        attempts.append({"word": expected_text, "score": score, "recorded_at": datetime.utcnow().isoformat(), "status": status_label})
        details["pronunciation"] = attempts[-50:]
        lp.details = details
        db.add(lp)

    db.commit()

    return {
        "score": score,
        "status": status_label,
        "feedback": feedback,
        "audio_url": audio_url,
        "word_id": word_obj.id if word_obj else None,
    }


@router.post("/mock-check")
def pronunciation_mock_check(
    payload: dict = Body(...),
    request: Request = None,
    db: Session = Depends(deps.current_db),
):
    deps.require_user(request, db=db)
    phrase = (payload.get("phrase") or "").strip()
    language = (payload.get("language") or "kk").lower()
    if not phrase:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="phrase is required")

    feedback_ru = "Отлично сказано! Продолжай в том же духе."
    feedback_kk = "Жарайсың! Дұрыс айттың, осылай жалғастыр."
    tips = ["Держи темп", "Чётко выговаривай согласные"] if language == "ru" else ["Жылдамдығыңды сақта", "Дыбыстарды анық айт"]

    return {
        "ok": True,
        "score": 9,
        "status": "excellent",
        "feedback": feedback_ru if language == "ru" else feedback_kk,
        "tips": tips,
        "phrase": phrase,
    }


@router.post("/check-audio")
async def pronunciation_check_audio(
    request: Request,
    audio: UploadFile = File(...),
    word: str = Form(...),
    language: str = Form(default="kk"),
    db: Session = Depends(deps.current_db),
):
    """Simple audio pronunciation check - accepts real audio recording and returns mock feedback"""
    user = deps.require_user(request, db=db)
    
    # Read audio file (we're not analyzing it, just accepting it)
    audio_data = await audio.read()
    if not audio_data or len(audio_data) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio file is empty")
    
    # Mock feedback - could be enhanced later with real analysis
    language = language.lower()
    
    # Random score between 70-100 for demo purposes
    import random
    score = random.randint(70, 100)
    
    if score >= 85:
        status_label = "excellent"
        feedback_ru = "🌟 Отлично! Произношение чёткое и правильное!"
        feedback_kk = "🌟 Өте жақсы! Дыбыстауыңыз нақты және дұрыс!"
        tips = ["Продолжай в том же духе!", "Отличная дикция!"]
    elif score >= 70:
        status_label = "good"
        feedback_ru = "✅ Хорошо! Ещё немного практики и будет идеально."
        feedback_kk = "✅ Жақсы! Тағы бір аз тәжірибе және керемет болады."
        tips = ["Говори чуть медленнее", "Отчётливее произноси гласные"]
    elif score >= 50:
        status_label = "ok"
        feedback_ru = "⚠️ Неплохо, но нужно ещё потренироваться."
        feedback_kk = "⚠️ Ажарлы, бірақ тағы да жаттықтыру қажет."
        tips = ["Прослушай образец ещё раз", "Попробуй записать медленнее"]
    else:
        status_label = "bad"
        feedback_ru = "❌ Попробуй ещё раз. Прослушай образец внимательнее."
        feedback_kk = "❌ Қайтадан көрісіп. Үлгіні мұқият тыңда."
        tips = ["Повтори образец несколько раз", "Говори чётче и громче"]
    
    feedback = feedback_ru if language == "ru" else feedback_kk
    
    return {
        "score": score,
        "status": status_label,
        "feedback": feedback,
        "tips": tips,
        "word": word,
    }



@router.post("/check-audio")
async def check_audio(
    request: Request,
    audio: UploadFile = File(...),
    word: str = Form(...),
    language: str = Form(default="kk"),
    db: Session = Depends(deps.current_db),
):
    """Check pronunciation from real audio recording"""
    user = deps.require_user(request, db=db)
    
    if not word or not word.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="word is required")
    
    # Read audio file
    audio_content = await audio.read()
    if not audio_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="audio file is empty")
    
    # Evaluate pronunciation using real service
    score, status_label = evaluate_pronunciation(word.strip(), audio_content, language)
    feedback = feedback_for_score(score, language)
    tips = []
    
    # Generate helpful tips based on score
    if language == "kk":
        if score < 0.5:
            tips = ["Дыбыстарды анық айт", "Жылдамдығыңды төмендет", "Үндеулерді ұзына айт"]
        elif score < 0.75:
            tips = ["Тағы бір рет байқап тыңда", "Дұрыс ырғақ сақта"]
        else:
            tips = ["Жарайсың! Осылай жалғастыр"]
    else:
        if score < 0.5:
            tips = ["Чётко выговаривай каждый звук", "Замедли темп", "Вытягивай гласные"]
        elif score < 0.75:
            tips = ["Послушай еще раз", "Сохраняй правильный ударение"]
        else:
            tips = ["Отлично! Продолжай так"]
    
    return {
        "score": int(score * 100),  # Return 0-100
        "status": status_label,
        "feedback": feedback,
        "tips": tips,
        "word": word,
        "language": language,
    }
