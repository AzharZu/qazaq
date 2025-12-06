import random
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from .. import models

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
        "word": str(word or "").strip(),
        "translation": str(translation or "").strip(),
        "definition": str(definition or "").strip(),
        "example_sentence": str(example_sentence or "").strip(),
        "image_url": image_url,
        "audio_url": audio_url,
    }


def add_word_to_dictionary(user_id: int, course_id: int, word_data, db: Session) -> Optional[models.VocabularyWord]:
    """Add a word from lesson interactions into the user's vocabulary."""
    fields = _extract_word_fields(word_data)
    if not fields["word"] or not fields["translation"]:
        return None

    existing = (
        db.query(models.VocabularyWord)
        .filter(
            models.VocabularyWord.user_id == user_id,
            models.VocabularyWord.course_id == course_id,
            func.lower(models.VocabularyWord.word) == fields["word"].lower(),
        )
        .first()
    )
    if existing:
        return existing

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
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    _invalidate_cache(user_id)
    return entry


def add_flashcards_to_dictionary(user_id: int, course_id: int, flashcards: List[models.Flashcard], db: Session) -> int:
    """Backwards-compatible helper to add flashcards (used when opening a lesson)."""
    added = 0
    for card in flashcards or []:
        if add_word_to_dictionary(user_id, course_id, card, db):
            added += 1
    return added


def get_user_vocabulary(user_id: int, db: Session, include_learned: bool = False) -> List[models.VocabularyWord]:
    cache_key = (user_id, include_learned)
    now = _now()
    cached = _cache_ids.get(cache_key)
    ids: List[int] = []
    if cached and now - cached["ts"] < _CACHE_TTL:
        ids = cached.get("ids", [])

    query = (
        db.query(models.VocabularyWord)
        .options(selectinload(models.VocabularyWord.course))
        .filter(models.VocabularyWord.user_id == user_id)
    )
    if ids:
        words = query.filter(models.VocabularyWord.id.in_(ids)).order_by(models.VocabularyWord.created_at.asc()).all()
    else:
        if not include_learned:
            query = query.filter(models.VocabularyWord.learned.is_(False))
        words = query.order_by(models.VocabularyWord.created_at.asc()).all()
        _cache_ids[cache_key] = {"ts": now, "ids": [w.id for w in words]}
    return words


def get_user_dictionary_grouped(user_id: int, db: Session, include_learned: bool = False) -> Dict[str, List[models.VocabularyWord]]:
    rows = get_user_vocabulary(user_id, db, include_learned=include_learned)
    grouped: Dict[str, List[models.VocabularyWord]] = {}
    for row in rows:
        key = row.course.name if row.course else f"Курс {row.course_id}"
        grouped.setdefault(key, []).append(row)
    return grouped


def get_neighbor_word(user_id: int, current_id: Optional[int], direction: str, db: Session) -> Optional[models.VocabularyWord]:
    words = get_user_vocabulary(user_id, db)
    if not words:
        return None
    if current_id is None:
        return words[0]
    ids = [w.id for w in words]
    try:
        idx = ids.index(current_id)
    except ValueError:
        idx = 0
    if direction == "prev":
        next_idx = (idx - 1) % len(words)
    else:
        next_idx = (idx + 1) % len(words)
    return words[next_idx]


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
    per_course_rows = (
        db.query(models.VocabularyWord.course_id, models.Course.name, func.count(models.VocabularyWord.id))
        .join(models.Course, models.Course.id == models.VocabularyWord.course_id, isouter=True)
        .filter(models.VocabularyWord.user_id == user_id)
        .group_by(models.VocabularyWord.course_id, models.Course.name)
        .all()
    )
    course_counts = {row[1] or f"Курс {row[0]}": row[2] for row in per_course_rows}
    hardest_items = hardest_words(user_id, db, 5)
    hardest = [
        {
            "id": w.id,
            "word": w.word,
            "translation": w.translation,
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
