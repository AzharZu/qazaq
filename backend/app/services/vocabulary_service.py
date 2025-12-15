import hashlib
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from gtts import gTTS
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ..db import models
from ..utils.encoding_fix import clean_encoding

AUDIO_DIR = Path(__file__).resolve().parents[1] / "static" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MODES = {"repeat", "mc", "write", "multiple_choice"}
_CACHE_TTL = timedelta(seconds=45)
_cache_ids: dict[tuple[int, bool], dict] = {}


def _now() -> datetime:
    return datetime.utcnow()


def _invalidate_cache(user_id: int, include_learned: Optional[bool] = None) -> None:
    keys = [k for k in _cache_ids if k[0] == user_id and (include_learned is None or k[1] == include_learned)]
    for key in keys:
        _cache_ids.pop(key, None)


def _extract_word_fields(word_data) -> dict:
    as_dict = word_data if isinstance(word_data, dict) else {}
    get = as_dict.get if isinstance(word_data, dict) else lambda k, default=None: getattr(word_data, k, default)
    word = get("word") or get("front") or ""
    translation = get("translation") or get("back") or ""
    definition = get("definition") or get("description") or translation
    example_sentence = get("example_sentence") or get("example") or ""
    image_url = get("image_url") or None
    audio_url = get("audio_url") or None
    return {
        "word": clean_encoding(str(word or "").strip()),
        "translation": clean_encoding(str(translation or "").strip()),
        "definition": clean_encoding(str(definition or "").strip()),
        "example_sentence": clean_encoding(str(example_sentence or "").strip()),
        "image_url": image_url,
        "audio_url": audio_url,
    }


def add_word_to_dictionary(
    user_id: int,
    course_id: int,
    word_data,
    db: Session,
    *,
    source_lesson_id: Optional[int] = None,
    source_block_id: Optional[int] = None,
    status: str = "new",
) -> Tuple[Optional[models.VocabularyWord], bool]:
    fields = _extract_word_fields(word_data)
    if not fields["word"] or not fields["translation"]:
        return None, False

    existing = (
        db.query(models.VocabularyWord)
        .filter(
            models.VocabularyWord.user_id == user_id,
            func.lower(models.VocabularyWord.word) == fields["word"].lower(),
        )
        .first()
    )
    if existing:
        updated = False
        if source_lesson_id and not existing.source_lesson_id:
            existing.source_lesson_id = source_lesson_id
            updated = True
        if source_block_id and not existing.source_block_id:
            existing.source_block_id = source_block_id
            updated = True
        if not existing.status:
            existing.status = status
            updated = True
        if updated:
            db.add(existing)
            db.commit()
            db.refresh(existing)
        return existing, False

    entry = models.VocabularyWord(
        user_id=user_id,
        course_id=course_id,
        word=fields["word"],
        translation=fields["translation"],
        definition=fields["definition"],
        example_sentence=fields["example_sentence"],
        image_url=fields["image_url"],
        audio_url=fields["audio_url"],
        learned=False,
        status=status or "new",
        source_lesson_id=source_lesson_id,
        source_block_id=source_block_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    _invalidate_cache(user_id)
    # optional compatibility link to user_dictionary
    if course_id:
        existing_link = (
            db.query(models.UserDictionary)
            .filter(
                models.UserDictionary.user_id == user_id,
                func.lower(models.UserDictionary.word) == fields["word"].lower(),
            )
            .first()
        )
        if not existing_link:
            link = models.UserDictionary(
                user_id=user_id,
                course_id=course_id,
                word=fields["word"],
                translation=fields["translation"],
                example=fields["example_sentence"],
                image_url=fields["image_url"],
                source_lesson_id=source_lesson_id,
                source_block_id=source_block_id,
                status=status or "new",
            )
            db.add(link)
            db.commit()
    return entry, True


def get_user_vocabulary(user_id: int, db: Session):
    return (
        db.query(models.VocabularyWord)
        .filter(models.VocabularyWord.user_id == user_id)
        .order_by(models.VocabularyWord.id.asc())
        .all()
    )


def derive_status(word: models.VocabularyWord, progress: dict) -> str:
    if getattr(word, "status", None):
        return word.status
    if getattr(word, "learned", False):
        return "learned"
    success = progress.get("success", 0)
    fails = progress.get("fails", 0)
    if success > fails:
        return "learning"
    return "new"


def extract_words_from_blocks(blocks: List[dict]) -> List[dict]:
    words: List[dict] = []
    for block in blocks or []:
        btype = (block.get("type") or block.get("block_type") or "").lower()
        content = block.get("content") or block.get("data") or {}
        if btype == "flashcards":
            for card in content.get("cards") or []:
                words.append(
                    {
                        "word": card.get("word") or card.get("front"),
                        "translation": card.get("translation") or card.get("back"),
                        "example": card.get("example") or card.get("example_sentence"),
                        "image_url": card.get("image_url"),
                        "audio_url": card.get("audio_url"),
                        "source_block_id": block.get("id"),
                    }
                )
        elif btype == "pronunciation":
            for item in content.get("items") or []:
                words.append(
                    {
                        "word": item.get("word"),
                        "translation": item.get("translation") or item.get("expected_pronunciation"),
                        "example": item.get("example") or item.get("example_sentence"),
                        "image_url": item.get("image_url"),
                        "audio_url": item.get("audio_url"),
                        "source_block_id": block.get("id"),
                    }
                )
    return words


def sync_lesson_vocabulary(user_id: int, lesson: models.Lesson, blocks: List[dict], db: Session) -> int:
    """Sync flashcard/pronunciation words into user's dictionary. Returns count of newly added words."""
    if not lesson or not lesson.module or not lesson.module.course:
        return 0
    course_id = lesson.module.course.id
    seen: set[str] = set()
    existing = {
        (w.word or "").strip().lower(): w
        for w in db.query(models.VocabularyWord).filter(models.VocabularyWord.user_id == user_id).all()
    }
    added = 0
    for item in extract_words_from_blocks(blocks):
        key = (item.get("word") or "").strip().lower()
        if not key or key in seen or key in existing:
            continue
        seen.add(key)
        _, created = add_word_to_dictionary(
            user_id,
            course_id,
            item,
            db,
            source_lesson_id=lesson.id,
            source_block_id=item.get("source_block_id"),
            status="new",
        )
        if created:
            added += 1
            existing[key] = True
    return added


def fetch_user_dictionary(user_id: int, db: Session, lesson_id: Optional[int] = None) -> List[models.VocabularyWord]:
    query = db.query(models.VocabularyWord).filter(models.VocabularyWord.user_id == user_id)
    if lesson_id:
        query = query.filter(models.VocabularyWord.source_lesson_id == lesson_id)
    # Order: new -> learning -> learned, then recent first
    status_priority = {"new": 0, "learning": 1, "learned": 2}
    words = query.all()
    return sorted(words, key=lambda w: (status_priority.get(w.status or "", 1), -(w.id or 0)))


def mark_word_learned(word_id: int, user_id: int, db: Session) -> bool:
    word = (
        db.query(models.VocabularyWord)
        .filter(models.VocabularyWord.id == word_id, models.VocabularyWord.user_id == user_id)
        .first()
    )
    if not word:
        return False
    word.learned = True
    word.repeat_streak = 0
    word.mc_streak = 0
    word.write_streak = 0
    db.add(word)
    db.commit()
    _invalidate_cache(user_id)
    return True


def _update_streak(word: models.VocabularyWord, mode: str, correct: bool) -> None:
    streak_field = {
        "repeat": "repeat_streak",
        "mc": "mc_streak",
        "write": "write_streak",
    }.get(mode, "repeat_streak")

    current_value = getattr(word, streak_field, 0) or 0
    if correct:
        setattr(word, streak_field, current_value + 1)
        word.correct_attempts = (word.correct_attempts or 0) + 1
    else:
        setattr(word, streak_field, 0)
        word.wrong_attempts = (word.wrong_attempts or 0) + 1


def process_game_result(word: models.VocabularyWord, mode: str, correct: bool, db: Session) -> models.VocabularyWord:
    _update_streak(word, mode, correct)
    thresholds = {"repeat": 3, "write": 3, "mc": 5}
    if correct and getattr(word, f"{mode}_streak") >= thresholds.get(mode, 3):
        word.learned = True
        word.status = "learned"
    else:
        # promote to learning on any attempt
        if not word.status or word.status == "new":
            word.status = "learning"
    word.last_practiced_at = _now()
    db.add(word)
    db.commit()
    db.refresh(word)
    _invalidate_cache(word.user_id)
    return word


def pick_training_word(user_id: int, db: Session, explicit_id: Optional[int] = None) -> Optional[models.VocabularyWord]:
    if explicit_id:
        word = (
            db.query(models.VocabularyWord)
            .filter(models.VocabularyWord.id == explicit_id, models.VocabularyWord.user_id == user_id)
            .first()
        )
        return word if word and not word.learned else None

    words = get_user_vocabulary(user_id, db)
    if not words:
        return None
    return random.choice(words)


def build_mc_question(word: models.VocabularyWord, db: Session) -> dict:
    options = mc_options(word, db)
    correct_value = clean_encoding(word.translation)
    try:
        correct_index = options.index(correct_value)
    except ValueError:
        correct_index = 0
    return {
        "question": clean_encoding(word.word),
        "options": options,
        "correct": correct_index,
        "word_id": word.id,
    }


def hardest_words(user_id: int, db: Session, limit: int = 5) -> List[models.VocabularyWord]:
    return (
        db.query(models.VocabularyWord)
        .filter(models.VocabularyWord.user_id == user_id)
        .order_by(models.VocabularyWord.wrong_attempts.desc(), models.VocabularyWord.created_at.asc())
        .limit(limit)
        .all()
    )


def get_stats(user_id: int, db: Session) -> dict:
    total = db.query(func.count(models.VocabularyWord.id)).filter(models.VocabularyWord.user_id == user_id).scalar() or 0
    learned = (
        db.query(func.count(models.VocabularyWord.id))
        .filter(models.VocabularyWord.user_id == user_id, models.VocabularyWord.learned.is_(True))
        .scalar()
        or 0
    )
    course_counts = {}
    hardest_items = hardest_words(user_id, db, 5)
    hardest = [
        {
            "id": w.id,
            "word": clean_encoding(w.word),
            "translation": clean_encoding(w.translation),
            "wrong_attempts": w.wrong_attempts or 0,
            "correct_attempts": w.correct_attempts or 0,
        }
        for w in hardest_items
    ]
    avg_success = 0
    correct_sum = (
        db.query(func.sum(models.VocabularyWord.correct_attempts)).filter(models.VocabularyWord.user_id == user_id).scalar() or 0
    )
    wrong_sum = (
        db.query(func.sum(models.VocabularyWord.wrong_attempts)).filter(models.VocabularyWord.user_id == user_id).scalar() or 0
    )
    total_attempts = correct_sum + wrong_sum
    if total_attempts:
        avg_success = int((correct_sum / total_attempts) * 100)
    return {
        "total": total,
        "learned": learned,
        "per_course": course_counts,
        "avg_success": avg_success,
        "hardest": hardest,
    }


def ensure_word_of_week(db: Session) -> Optional[models.WordOfTheWeek]:
    today = date.today()
    current = (
        db.query(models.WordOfTheWeek)
        .filter(models.WordOfTheWeek.start_date <= today, models.WordOfTheWeek.end_date >= today)
        .order_by(models.WordOfTheWeek.start_date.desc())
        .first()
    )
    if current:
        return current

    popular_subq = (
        db.query(models.VocabularyWord.word, func.count(models.VocabularyWord.id).label("cnt"))
        .group_by(models.VocabularyWord.word)
        .order_by(func.count(models.VocabularyWord.id).desc())
        .limit(1)
        .subquery()
    )
    candidate = (
        db.query(models.VocabularyWord)
        .join(popular_subq, models.VocabularyWord.word == popular_subq.c.word)
        .order_by(models.VocabularyWord.created_at.desc())
        .first()
    )
    if not candidate:
        return None

    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    entry = models.WordOfTheWeek(
        word_id=candidate.id,
        start_date=start,
        end_date=end,
        stats_views=0,
        stats_correct_answers=0,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def bump_word_of_week_view(word_of_week: models.WordOfTheWeek, db: Session) -> None:
    word_of_week.stats_views = (word_of_week.stats_views or 0) + 1
    db.add(word_of_week)
    db.commit()


def bump_word_of_week_correct(word_of_week: models.WordOfTheWeek, db: Session) -> None:
    word_of_week.stats_correct_answers = (word_of_week.stats_correct_answers or 0) + 1
    db.add(word_of_week)
    db.commit()


def normalize_audio_url(audio_url: str | None) -> str:
    url = audio_url or ""
    if url.startswith("/static/audio/"):
        return url.replace("/static/audio/", "/api/vocabulary/audio/")
    return url


def serialize_word(word: models.VocabularyWord | None) -> dict:
    if not word:
        return {}
    return {
        "id": word.id,
        "word": clean_encoding(word.word),
        "translation": clean_encoding(word.translation),
        "definition": clean_encoding(word.definition or ""),
        "example_sentence": clean_encoding(word.example_sentence or ""),
        "audio_url": normalize_audio_url(word.audio_url),
        "image_url": word.image_url or "",
        "course_id": word.course_id,
        "learned": bool(word.learned),
    }


def mc_options(word: models.VocabularyWord, db: Session) -> list[str]:
    options = {clean_encoding(word.translation)}
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
            options.add(clean_encoding(candidate))
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
                options.add(clean_encoding(row[0]))
    while len(options) < 4:
        options.add(f"{word.translation} ({len(options)})")
    options_list = list(options)
    random.shuffle(options_list)
    return options_list


def tts_for_word(user_id: int, text: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Word is empty")
    digest = hashlib.sha1(f"{user_id}:{cleaned}".encode()).hexdigest()[:16]
    filename = f"{user_id}-{digest}.mp3"
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        tts = gTTS(text=cleaned, lang="kk")
        tts.save(filepath)
    return f"/api/vocabulary/audio/{filename}"
