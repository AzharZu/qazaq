from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .lesson import LessonSummary
from .module import ModuleOut


class CourseCreate(BaseModel):
    slug: str
    name: str
    description: str
    audience: str


class CourseUpdate(BaseModel):
    slug: str | None = None
    name: str | None = None
    description: str | None = None
    audience: str | None = None


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str
    audience: str
    modules: List[ModuleOut] = Field(default_factory=list)


class CourseWithProgress(CourseOut):
    progress_percent: int = 0
    next_lesson: Optional[LessonSummary] = None
    progress_map: dict = Field(default_factory=dict)


__all__ = ["CourseOut", "CourseWithProgress", "CourseCreate", "CourseUpdate"]
