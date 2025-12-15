from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AutoCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Learner submission")
    mode: Literal["translation", "pronunciation", "grammar"] = "translation"
    language: Literal["kk", "ru", "en"] | str = "kk"
    audio_base64: Optional[str] = Field(default=None, description="Optional audio in base64")


class AutoCheckCorrection(BaseModel):
    issue: str
    suggestion: str


class AutoCheckResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    score: int = Field(0, ge=0, le=100)
    corrections: list[AutoCheckCorrection] = Field(default_factory=list)
    explanation: str = ""
    suggestions: list[str] = Field(default_factory=list)
    audio_url: Optional[str] = None


__all__ = ["AutoCheckRequest", "AutoCheckCorrection", "AutoCheckResponse"]
