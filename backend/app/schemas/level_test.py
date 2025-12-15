from typing import List, Optional
from pydantic import BaseModel


class LevelTestOptionOut(BaseModel):
    id: int
    text: str
    order: int


class LevelTestQuestionOut(BaseModel):
    id: int
    text: str
    example: Optional[str] = None
    correct_index: int
    options: List[LevelTestOptionOut]


class LevelTestAnswer(BaseModel):
    question_id: int
    selected: int


class LevelTestResult(BaseModel):
    level: str
    recommended_course: str


__all__ = ["LevelTestQuestionOut", "LevelTestResult", "LevelTestAnswer"]
