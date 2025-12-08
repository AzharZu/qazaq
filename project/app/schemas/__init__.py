from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    age: int
    target: str
    daily_minutes: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    age: int
    target: str
    daily_minutes: int
    level: Optional[str] = None


class PlacementResultCreate(BaseModel):
    user_id: Optional[int]
    level: str
    score: int


class PlacementResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    level: str
    score: int
    created_at: datetime


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str
    audience: str


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    name: str
    order: int
    description: Optional[str]


class LessonBlockContent(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    items: Optional[List[str]] = None
    dialogue: Optional[List[dict]] = None


class LessonBlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    block_type: str
    content: dict
    order: int


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    title: str
    description: Optional[str]
    order: int
    blocks: List[LessonBlockOut] = Field(default_factory=list)

# Lesson editor v2 schemas
from .lesson_editor import (  # noqa: E402,F401
    BlockCreate,
    BlockOut as LessonEditorBlockOut,
    BlockType,
    BlockUpdate,
    LessonUpdate,
    LessonWithBlocksOut,
    ReorderBlocks,
)
