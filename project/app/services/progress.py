from typing import Dict, List

from sqlalchemy.orm import Session, selectinload

from .. import models


def get_progress_for_user(db: Session, user_id: int) -> Dict:
    """Return course-level progress for user."""
    course = (
        db.query(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.Module.lessons))
        .join(models.Module, models.Module.course_id == models.Course.id)
        .join(models.Lesson, models.Lesson.module_id == models.Module.id)
        .first()
    )
    if not course:
        return {
            "course_title": "",
            "completed_lessons": 0,
            "total_lessons": 0,
            "percent": 0,
            "completed_modules": [],
            "certificates": [],
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
    for m in course.modules:
        module_lessons = [l for l in m.lessons]
        for l in module_lessons:
            if progress_map.get(l.id) == "done":
                completed_lesson_titles.append(l.title)
        if module_lessons and all(progress_map.get(l.id) == "done" for l in module_lessons):
            completed_modules.append(m)
            completed_module_names.append(m.name or f"Модуль {m.order}")
            certificates.append({"id": m.id, "title": m.name or f"Модуль {m.order}"})

    return {
        "course_title": course.name,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "percent": percent,
        "completed_modules": completed_modules,
        "completed_module_names": completed_module_names,
        "completed_lesson_titles": completed_lesson_titles,
        "certificates": certificates,
    }
