from typing import Dict, List, Optional

from sqlalchemy.orm import Session, selectinload

from .. import models
from .courses import recommend_course_slug


def _pick_course(
    db: Session, course_slug: Optional[str], age: Optional[int] = None, target: Optional[str] = None
) -> Optional[models.Course]:
    query = db.query(models.Course).options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
    if course_slug:
        course = query.filter(models.Course.slug == course_slug).first()
        if course:
            return course
    recommended_slug = recommend_course_slug(age, target) if (age or target) else None
    if recommended_slug:
        course = query.filter(models.Course.slug == recommended_slug).first()
        if course:
            return course
    return query.first()


def get_progress_for_user(db: Session, user_id: int, course_slug: Optional[str] = None) -> Dict:
    """Return course-level progress for user for the selected/recommended course."""
    user = db.get(models.User, user_id)
    course = _pick_course(db, course_slug, getattr(user, "age", None), getattr(user, "target", None))
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

    lessons = [l for m in course.modules for l in m.lessons]
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

    completed_modules: List[models.Module] = []
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
                completed_lesson_titles.append(l.title)
        if module_lessons and all(progress_map.get(l.id) == "done" for l in module_lessons):
            completed_modules.append(m)
            completed_module_names.append(m.name or f"Модуль {m.order}")
            certificates.append({"id": m.id, "title": m.name or f"Модуль {m.order}"})

    if not next_lesson and course.modules and course.modules[0].lessons:
        next_lesson = course.modules[0].lessons[0]

    return {
        "course_id": course.id,
        "course_slug": course.slug,
        "course_title": course.name,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "percent": percent,
        "completed_modules": completed_modules,
        "completed_module_names": completed_module_names,
        "completed_lesson_titles": completed_lesson_titles,
        "certificates": certificates,
        "next_lesson": next_lesson,
        "progress_map": progress_map,
    }
