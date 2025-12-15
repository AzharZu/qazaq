from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .lesson import LessonSummary


class ModuleCreate(BaseModel):
    course_id: int
    name: str
    order: int | None = None
    description: Optional[str] = None


class ModuleUpdate(BaseModel):
    course_id: Optional[int] = None
    name: Optional[str] = None
    order: Optional[int] = None
    description: Optional[str] = None


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    name: str
    order: int
    description: Optional[str] = None
    lessons: List[LessonSummary] = Field(default_factory=list)


__all__ = ["ModuleOut", "ModuleCreate", "ModuleUpdate"]
