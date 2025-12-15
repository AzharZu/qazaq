from typing import List, Optional

from pydantic import BaseModel, Field


class PlacementQuestion(BaseModel):
    id: str
    prompt: str
    options: List[str]
    correct_option: int
    section: Optional[str] = None


class PlacementQuestionsResponse(BaseModel):
    questions: List[PlacementQuestion] = Field(default_factory=list)
    total: int = 0


class PlacementAnswerPayload(BaseModel):
    question_id: str
    selected_option: int


class PlacementFinishPayload(BaseModel):
    answers: List[PlacementAnswerPayload] = Field(default_factory=list)
    limit: int = 20


class PlacementResult(BaseModel):
    level: str
    recommended_course: str
    score: int
    total: int
    raw_score: int


__all__ = [
    "PlacementQuestion",
    "PlacementQuestionsResponse",
    "PlacementAnswerPayload",
    "PlacementFinishPayload",
    "PlacementResult",
]
