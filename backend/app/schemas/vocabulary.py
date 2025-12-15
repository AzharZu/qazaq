from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VocabularyWordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    word: str
    translation: str
    definition: str | None = None
    example_sentence: str | None = None
    audio_url: str | None = None
    image_url: str | None = None
    course_id: int
    learned: bool = False


class VocabularyStats(BaseModel):
    total: int
    learned: int
    per_course: dict
    avg_success: int
    hardest: list[dict]


class VocabularyGameRound(BaseModel):
    word: VocabularyWordOut | dict
    options: list[str] = Field(default_factory=list)


class VocabularyCheckResponse(BaseModel):
    correct: bool
    hint: str
    streak: int
    learned: bool
    correct_answer: str


__all__ = [
    "VocabularyWordOut",
    "VocabularyStats",
    "VocabularyGameRound",
    "VocabularyCheckResponse",
]
