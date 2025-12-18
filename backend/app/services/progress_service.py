from datetime import datetime
from math import ceil
from typing import Any, Dict, Optional, List

from sqlalchemy.orm import Session, selectinload

from ..db import models
from ..utils.encoding_fix import clean_encoding
from ..schemas.block import validate_block_payload


def recommend_course_slug(age: int | None, target: str | None, level: str | None = None) -> str:
    """
    Suggest a course slug based on the learner profile.
    Priority is the tested level, then age/target fallbacks for compatibility.
    """
    normalized_level = (level or "").upper()
    if normalized_level in {"A0", "A1", "A2"}:
        return "kazkids"
    if normalized_level == "B1":
        return "kazpro"
    if normalized_level in {"B2", "C1", "C2"}:
        return "qyzmet-qazaq"

    if age is not None and age <= 15:
        return "kazkids"
    if target in ("gov", "business"):
        return "qyzmet-qazaq"
    return "kazpro"


def serialize_lesson(lesson: models.Lesson) -> dict:
    return {
        "id": lesson.id,
        "title": clean_encoding(lesson.title),
        "description": clean_encoding(lesson.description),
        "order": lesson.order,
        "module_id": lesson.module_id,
        "status": getattr(lesson, "status", "draft"),
        "difficulty": getattr(lesson, "difficulty", None),
        "estimated_time": getattr(lesson, "estimated_time", None),
        "blocks_order": lesson.blocks_order or [],
        "video_type": getattr(lesson, "video_type", None),
        "video_url": getattr(lesson, "video_url", None),
        "language": getattr(lesson, "language", "kk"),
    }


def serialize_module(module: models.Module, include_unpublished: bool = False) -> dict:
    lessons = [
        l
        for l in module.lessons
        if not getattr(l, "is_deleted", False)
        and getattr(l, "status", "draft") != "archived"
        and (include_unpublished or getattr(l, "status", "draft") == "published")
    ]
    return {
        "id": module.id,
        "name": clean_encoding(module.name),
        "description": clean_encoding(module.description),
        "order": module.order,
        "course_id": module.course_id,
        "lessons": sorted([serialize_lesson(l) for l in lessons], key=lambda l: l["order"]),
    }


def serialize_course(course: models.Course) -> dict:
    return {
        "id": course.id,
        "slug": course.slug,
        "name": clean_encoding(course.name),
        "description": clean_encoding(course.description),
        "audience": course.audience,
        "modules": sorted([serialize_module(m) for m in course.modules], key=lambda m: m["order"]),
    }


def _serialize_flashcard(card: models.Flashcard) -> dict:
    return {
        "id": card.id,
        "front": clean_encoding(card.front),
        "back": clean_encoding(card.back),
        "image_url": card.image_url,
        "audio_path": getattr(card, "audio_path", None),
        "audio_url": card.audio_url,
        "order": card.order,
    }


def _serialize_quiz(quiz: models.Quiz) -> dict:
    return {
        "id": quiz.id,
        "question": clean_encoding(quiz.question),
        "options": clean_encoding(quiz.options),
        "correct_option": quiz.correct_option,
        "explanation": clean_encoding(quiz.explanation),
        "order": quiz.order,
    }


def _collect_flashcards(block_payload: dict | None, lesson: models.Lesson) -> list[dict]:
    payload = block_payload or {}
    cards = payload.get("cards") or payload.get("items") or []
    if not cards and getattr(lesson, "flashcards", None):
        cards = [_serialize_flashcard(c) for c in sorted(lesson.flashcards, key=lambda fc: fc.order)]
    normalized_cards: list[dict] = []
    for idx, card in enumerate(cards):
        word = card.get("word") or card.get("front") or ""
        translation = card.get("translation") or card.get("back") or ""
        example = card.get("example_sentence") or card.get("example") or ""
        normalized_cards.append(
            clean_encoding(
                {
                    "id": card.get("id"),
                    "word": word,
                    "translation": translation,
                    "example_sentence": example,
                    "example": example,
                    "image_url": card.get("image_url") or card.get("image"),
                    "audio_path": card.get("audio_path"),
                    "audio_url": card.get("audio_url"),
                    "order": card.get("order") or idx + 1,
                }
            )
        )
    return normalized_cards


def _pronunciation_from_cards(cards: list[dict]) -> list[dict]:
    items: list[dict] = []
    for idx, card in enumerate(cards):
        items.append(
            clean_encoding(
                {
                    "id": card.get("id"),
                    "word": card.get("word") or card.get("front"),
                    "translation": card.get("translation") or card.get("back"),
                    "example": card.get("example") or card.get("example_sentence"),
                    "image_url": card.get("image_url") or card.get("image"),
                    "audio_path": card.get("audio_path"),
                    "audio_url": card.get("audio_url"),
                    "order": card.get("order") or idx + 1,
                }
            )
        )
    return items


def ordered_blocks(lesson: models.Lesson) -> list[models.LessonBlock]:
    order_map = {bid: idx for idx, bid in enumerate(lesson.blocks_order or [])}
    blocks = [b for b in lesson.blocks if not getattr(b, "is_deleted", False)]
    return sorted(blocks, key=lambda b: (order_map.get(b.id, b.order), b.order, b.id))


def normalize_block(block: models.LessonBlock, lesson: models.Lesson) -> dict:
    if getattr(block, "is_deleted", False):
        return None

    payload = block.data or block.content or {}
    if block.block_type == "audio_theory":
        # Normalize to unified structure while keeping audio + markdown
        payload = {
            "audio_path": payload.get("audio_path"),
            "audio_url": payload.get("audio_url"),
            "markdown": payload.get("markdown"),
        }
    if block.block_type in {"audio_task", "audio-task"} and not payload and getattr(block, "audio_task", None):
        payload = {
            "audio_path": getattr(block.audio_task, "audio_path", None),
            "audio_url": block.audio_task.audio_url,
            "transcript": block.audio_task.transcript,
            "options": block.audio_task.options or [],
            "correct_answer": block.audio_task.correct_answer,
            "answer_type": block.audio_task.answer_type,
            "feedback": block.audio_task.feedback,
        }
    content: Dict[str, Any] = payload or {}
    cleaned = validate_block_payload(block.block_type, content)
    normalized: dict = {
        "id": block.id,
        "order": block.order,
        "type": block.block_type,
        "block_type": block.block_type,
        "content": {},
    }

    if block.block_type == "video":
        normalized["content"] = {
            "video_url": cleaned.get("video_url") or content.get("video_url") or content.get("url"),
            "thumbnail_url": cleaned.get("thumbnail_url") or content.get("thumbnail_url"),
            "caption": clean_encoding(cleaned.get("caption") or content.get("caption")),
        }
    elif block.block_type == "theory":
        normalized["content"] = {
            "title": clean_encoding(cleaned.get("title")),
            "rich_text": clean_encoding(cleaned.get("rich_text") or cleaned.get("markdown") or ""),
            "highlights": clean_encoding(cleaned.get("highlights") or []),
            "examples": clean_encoding(cleaned.get("examples") or []),
            "video_url": cleaned.get("video_url") or content.get("video_url") or content.get("url"),
            "thumbnail_url": cleaned.get("thumbnail_url") or content.get("thumbnail_url"),
        }
    elif block.block_type == "audio_theory":
        normalized["type"] = "audio_theory"
        normalized["block_type"] = "audio_theory"
        normalized["content"] = {
            "audio_path": cleaned.get("audio_path") or content.get("audio_path"),
            "audio_url": cleaned.get("audio_url") or content.get("audio_url"),
            "markdown": clean_encoding(cleaned.get("markdown") or ""),
        }
    elif block.block_type == "image":
        normalized["content"] = {
            "image_url": cleaned.get("image_url") or content.get("url"),
            "explanation": clean_encoding(cleaned.get("explanation")),
            "keywords": clean_encoding(cleaned.get("keywords") or []),
        }
    elif block.block_type == "audio":
        normalized["content"] = {
            "audio_path": cleaned.get("audio_path") or content.get("audio_path"),
            "audio_url": cleaned.get("audio_url") or content.get("audio_url"),
            "transcript": clean_encoding(cleaned.get("transcript") or ""),
            "translation": clean_encoding(cleaned.get("translation") or ""),
        }
    elif block.block_type in {"audio_task", "audio-task"}:
        normalized["type"] = "audio_task"
        normalized["block_type"] = "audio_task"
        normalized["content"] = {
            "audio_path": cleaned.get("audio_path") or content.get("audio_path") or getattr(block.audio_task, "audio_path", None),
            "audio_url": cleaned.get("audio_url") or content.get("audio_url") or getattr(block.audio_task, "audio_url", None),
            "transcript": clean_encoding(cleaned.get("transcript") or ""),
            "options": cleaned.get("options") or [],
            # do not expose correct_answer to students
        }
    elif block.block_type == "flashcards":
        cards = _collect_flashcards(cleaned, lesson)
        normalized["content"] = {"cards": cards}
    elif block.block_type == "pronunciation":
        cards = _collect_flashcards(cleaned, lesson)
        items = cleaned.get("items") or cleaned.get("words") or _pronunciation_from_cards(cards)
        normalized["content"] = {
            "phrase": clean_encoding(cleaned.get("phrase")),
            "sample_audio_url": cleaned.get("sample_audio_url"),
            "expected_pronunciation": clean_encoding(cleaned.get("expected_pronunciation")),
            "word_id": cleaned.get("word_id") or content.get("word_id"),
            "items": items,
        }
    elif block.block_type in {"theory_quiz", "quiz"}:
        normalized["type"] = "theory_quiz"
        normalized["block_type"] = "theory_quiz"
        normalized["content"] = cleaned or content
    elif block.block_type == "lesson_test":
        normalized["content"] = cleaned
    elif block.block_type == "free_writing":
        normalized["content"] = {
            "question": clean_encoding(cleaned.get("question") or content.get("question") or ""),
            "rubric": clean_encoding(cleaned.get("rubric") or content.get("rubric") or ""),
            "language": cleaned.get("language") or content.get("language") or getattr(lesson, "language", None),
        }
    else:
        normalized["content"] = clean_encoding(cleaned or content)

    normalized["content"] = clean_encoding(normalized["content"])
    # Keep a reference to raw data for admin/preview use-cases
    normalized["data"] = payload
    return normalized


def calculate_course_progress(db: Session, user: Optional[models.User], course: models.Course):
    lesson_ids = [
        lesson.id
        for module in course.modules
        for lesson in module.lessons
        if not getattr(lesson, "is_deleted", False) and getattr(lesson, "status", "draft") != "archived"
    ]
    progress_map = _get_progress_map(db, user.id if user else None, lesson_ids)
    if not lesson_ids:
        return 0, None, progress_map
    completed = sum(1 for lid in lesson_ids if progress_map.get(lid) == "done")
    progress_percent = int((completed / len(lesson_ids)) * 100) if lesson_ids else 0

    next_lesson = None
    for module in course.modules:
        for lesson in module.lessons:
            if progress_map.get(lesson.id) != "done":
                next_lesson = lesson
                break
        if next_lesson:
            break
    if not next_lesson and course.modules and course.modules[0].lessons:
        next_lesson = course.modules[0].lessons[0]
    return progress_percent, next_lesson, progress_map


def _get_progress_map(db: Session, user_id: int | None, lesson_ids: list[int]) -> dict[int, str]:
    if not user_id or not lesson_ids:
        return {}
    rows = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == user_id, models.UserProgress.lesson_id.in_(lesson_ids))
        .all()
    )
    return {row.lesson_id: row.status for row in rows}


def list_courses_with_progress(db: Session, user: Optional[models.User]):
    courses = (
        db.query(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
        .all()
    )
    payload = []
    for course in courses:
        percent, next_lesson, progress_map = calculate_course_progress(db, user, course)
        payload.append(
            {
                "course": course,
                "progress_percent": percent,
                "next_lesson": next_lesson,
                "progress_map": progress_map,
            }
        )
    return payload


def module_with_progress(db: Session, module_id: int, user: Optional[models.User]):
    module = (
        db.query(models.Module)
        .options(selectinload(models.Module.lessons))
        .filter(models.Module.id == module_id)
        .first()
    )
    if not module:
        return None, {}
    lesson_ids = [
        lesson.id
        for lesson in module.lessons
        if not getattr(lesson, "is_deleted", False) and getattr(lesson, "status", "draft") != "archived"
    ]
    progress_map = _get_progress_map(db, user.id if user else None, lesson_ids)
    return module, progress_map


def _ensure_user_progress(db: Session, user: models.User, lesson: models.Lesson) -> models.UserProgress:
    entry = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == user.id, models.UserProgress.lesson_id == lesson.id)
        .first()
    )
    if not entry:
        entry = models.UserProgress(user_id=user.id, lesson_id=lesson.id, status="in_progress")
        db.add(entry)
        db.commit()
        db.refresh(entry)
    return entry


def get_lesson_detail(db: Session, lesson_id: int, user: models.User, allow_unpublished: bool = False):
    lesson = (
        db.query(models.Lesson)
        .options(
            selectinload(models.Lesson.blocks),
            selectinload(models.Lesson.flashcards),
            selectinload(models.Lesson.quizzes),
            selectinload(models.Lesson.module)
            .selectinload(models.Module.course)
            .selectinload(models.Course.modules)
            .selectinload(models.Module.lessons),
            selectinload(models.Lesson.module).selectinload(models.Module.lessons),
        )
        .filter(models.Lesson.id == lesson_id)
        .filter(models.Lesson.is_deleted.is_(False))
        .filter(models.Lesson.status != "archived")
        .first()
    )
    if not lesson:
        return None
    if getattr(lesson, "is_deleted", False):
        return None
    if not allow_unpublished and getattr(lesson, "status", "draft") != "published":
        return None

    progress_entry = _ensure_user_progress(db, user, lesson)
    lesson_progress = (
        db.query(models.LessonProgress)
        .filter(models.LessonProgress.user_id == user.id, models.LessonProgress.lesson_id == lesson.id)
        .first()
    )
    course = (
        db.query(models.Course)
        .filter(models.Course.id == lesson.module.course.id)
        .first()
    ) or lesson.module.course

    lesson_ids = [l.id for m in course.modules for l in m.lessons] if course.modules else []
    progress_map = _get_progress_map(db, user.id, lesson_ids)

    completed = sum(1 for lid in lesson_ids if progress_map.get(lid) == "done") if lesson_ids else 0
    course_progress = int((completed / len(lesson_ids)) * 100) if lesson_ids else 0

    module_lessons = lesson.module.lessons
    module_completed = sum(1 for l in module_lessons if progress_map.get(l.id) == "done") if module_lessons else 0
    module_progress = int((module_completed / len(module_lessons)) * 100) if module_lessons else 0

    ordered_lessons = sorted(module_lessons, key=lambda l: l.order)
    current_index = next((idx for idx, l in enumerate(ordered_lessons) if l.id == lesson.id), None)
    prev_lesson = ordered_lessons[current_index - 1] if current_index and current_index > 0 else None
    next_lesson = ordered_lessons[current_index + 1] if current_index is not None and current_index + 1 < len(ordered_lessons) else None

    normalized_blocks = []
    for b in ordered_blocks(lesson):
        norm = normalize_block(b, lesson)
        if norm:
            normalized_blocks.append(norm)

    return {
        "lesson": lesson,
        "blocks": normalized_blocks,
        "progress_status": progress_entry.status,
        "score": lesson_progress.score if lesson_progress else None,
        "time_spent": (lesson_progress.time_spent if lesson_progress else None) or getattr(progress_entry, "time_spent", 0),
        "course_progress": course_progress,
        "module_progress": module_progress,
        "progress_map": progress_map,
        "navigation": {
            "prev_lesson_id": prev_lesson.id if prev_lesson else None,
            "next_lesson_id": next_lesson.id if next_lesson else None,
        },
    }


def level_score(score: int, total_questions: int) -> int:
    if total_questions == 0:
        return 0
    if total_questions == 20:
        return score
    return ceil(score * 20 / total_questions)


def get_progress_for_user(db: Session, user_id: int, course_slug: Optional[str] = None) -> Dict:
    user = db.get(models.User, user_id)
    course = None
    if course_slug:
        course = (
            db.query(models.Course)
            .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
            .filter(models.Course.slug == course_slug)
            .first()
        )
    if not course:
        course = (
            db.query(models.Course)
            .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
            .first()
        )
    if not course:
        return {
            "course_title": "",
            "course_slug": "",
            "course_id": None,
            "completed_lessons": 0,
            "total_lessons": 0,
            "percent": 0,
            "completed_modules": [],
            "completed_module_names": [],
            "completed_lesson_titles": [],
            "certificates": [],
            "next_lesson": None,
            "progress_map": {},
        }

    lessons = [
        l
        for m in course.modules
        for l in m.lessons
        if not getattr(l, "is_deleted", False) and getattr(l, "status", "draft") != "archived"
    ]
    lesson_ids = [l.id for l in lessons]
    progress_rows = (
        db.query(models.UserProgress)
        .filter(models.UserProgress.user_id == user_id, models.UserProgress.lesson_id.in_(lesson_ids))
        .all()
    )
    progress_map = {row.lesson_id: row.status for row in progress_rows}
    completed_lessons = sum(1 for lid in lesson_ids if progress_map.get(lid) == "done")
    total_lessons = len(lesson_ids) if lesson_ids else 0
    percent = int((completed_lessons / total_lessons) * 100) if total_lessons else 0

    completed_modules: List[dict] = []
    completed_module_names: List[str] = []
    completed_lesson_titles: List[str] = []
    certificates: List[dict] = []
    next_lesson = None
    for m in course.modules:
        module_lessons = [l for l in m.lessons]
        for l in module_lessons:
            if not next_lesson and progress_map.get(l.id) != "done":
                next_lesson = l
            if progress_map.get(l.id) == "done":
                completed_lesson_titles.append(clean_encoding(l.title))
        if module_lessons and all(progress_map.get(l.id) == "done" for l in module_lessons):
            completed_modules.append({"id": m.id, "name": clean_encoding(m.name), "order": m.order})
            completed_module_names.append(clean_encoding(m.name or f"Модуль {m.order}"))
            certificates.append({"id": m.id, "title": clean_encoding(m.name or f"Модуль {m.order}")})

    if not next_lesson and course.modules and course.modules[0].lessons:
        next_lesson = course.modules[0].lessons[0]

    return {
        "course_id": course.id,
        "course_slug": course.slug,
        "course_title": clean_encoding(course.name),
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "percent": percent,
        "completed_modules": completed_modules,
        "completed_module_names": completed_module_names,
        "completed_lesson_titles": completed_lesson_titles,
        "certificates": certificates,
        "next_lesson": serialize_lesson(next_lesson) if next_lesson else None,
        "progress_map": progress_map,
    }
