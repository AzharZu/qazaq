from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .block import LessonBlockOut, NormalizedBlock


class FlashcardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    front: str
    back: str
    image_url: Optional[str] = None
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    order: int


class QuizOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    options: list[str]
    correct_option: int
    explanation: Optional[str] = None
    order: int


class LessonSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    title: str
    order: int
    status: str
    difficulty: Optional[str] = None
    estimated_time: Optional[int] = None
    language: Optional[str] = None
    version: Optional[int] = None
    blocks_order: List[int] | None = None
    is_deleted: bool = False
    description: Optional[str] = None
    video_type: Optional[str] = None
    video_url: Optional[str] = None


class LessonOut(LessonSummary):
    blocks: List[LessonBlockOut] = Field(default_factory=list)


class LessonNavigation(BaseModel):
    prev_lesson_id: Optional[int] = None
    next_lesson_id: Optional[int] = None


class LessonDetail(BaseModel):
    lesson: LessonSummary
    blocks: List[NormalizedBlock] = Field(default_factory=list)
    flashcards: List[FlashcardOut] = Field(default_factory=list)
    quizzes: List[QuizOut] = Field(default_factory=list)
    progress_status: str
    score: Optional[int] = None
    time_spent: Optional[int] = None
    course_progress: int
    module_progress: int
    progress_map: dict
    navigation: LessonNavigation


class LessonCreate(BaseModel):
    module_id: int
    title: str
    description: Optional[str] = None
    status: str = "draft"
    difficulty: Optional[str] = None
    estimated_time: Optional[int] = None
    age_group: Optional[str] = None
    language: str = "kk"
    order: Optional[int] = None
    video_type: Optional[str] = "youtube"  # youtube, vimeo, file
    video_url: Optional[str] = None


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_time: Optional[int] = None
    age_group: Optional[str] = None
    language: Optional[str] = None
    version: Optional[int] = None
    blocks_order: Optional[List[int]] = None
    order: Optional[int] = None
    video_type: Optional[str] = None  # youtube, vimeo, file
    video_url: Optional[str] = None


__all__ = [
    "LessonSummary",
    "LessonOut",
    "LessonDetail",
    "FlashcardOut",
    "QuizOut",
    "LessonNavigation",
    "LessonCreate",
    "LessonUpdate",
]
