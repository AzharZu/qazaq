from typing import Any, Optional

from pydantic import BaseModel, Field

from .lesson import LessonSummary


class ProgressPayload(BaseModel):
    course_id: Optional[int]
    course_slug: str | None = None
    course_title: str | None = None
    completed_lessons: int = 0
    total_lessons: int = 0
    percent: int = 0
    completed_modules: list[Any] = Field(default_factory=list)
    completed_module_names: list[str] = Field(default_factory=list)
    completed_lesson_titles: list[str] = Field(default_factory=list)
    certificates: list[Any] = Field(default_factory=list)
    next_lesson: LessonSummary | dict | None = None
    progress_map: dict = Field(default_factory=dict)
    xp_total: int = 0
    xp_today: int = 0
    streak_days: int = 0
    goal_today: dict = Field(default_factory=dict)


__all__ = ["ProgressPayload"]
