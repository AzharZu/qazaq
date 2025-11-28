from sqlalchemy.orm import Session

from .. import models


def add_flashcards_to_dictionary(user_id: int, course_id: int, flashcards: list[models.Flashcard], db: Session) -> int:
    """Add flashcards to user dictionary once."""
    if not flashcards:
        return 0
    existing = (
        db.query(models.UserDictionary.word)
        .filter(models.UserDictionary.user_id == user_id, models.UserDictionary.course_id == course_id)
        .all()
    )
    existing_words = {row[0] for row in existing}
    added = 0
    for card in flashcards:
        if card.front in existing_words:
            continue
        entry = models.UserDictionary(
            user_id=user_id,
            course_id=course_id,
            word=card.front,
            translation=card.back,
            example=card.image_url or None,
        )
        db.add(entry)
        added += 1
    if added:
        db.commit()
    return added


def get_user_dictionary_grouped(user_id: int, db: Session) -> dict:
    rows = (
        db.query(models.UserDictionary)
        .join(models.Course, models.Course.id == models.UserDictionary.course_id)
        .filter(models.UserDictionary.user_id == user_id)
        .all()
    )
    grouped: dict[str, list[models.UserDictionary]] = {}
    for row in rows:
        key = row.course.name if row.course else str(row.course_id)
        grouped.setdefault(key, []).append(row)
    return grouped
