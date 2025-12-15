from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

BlockType = Literal[
    "video",
    "theory",
    "audio_theory",
    "theory_quiz",
    "lesson_test",
    "image",
    "audio",
    "flashcards",
    "pronunciation",
    "audio_task",
    # compatibility buckets
    "quiz",
    "example",
    "assignment",
    "mascot_tip",
    "dragdrop",
    "story",
]


class ExampleItem(BaseModel):
    text: str
    translation: str


class VideoBlockPayload(BaseModel):
    video_url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None


class TheoryBlockPayload(BaseModel):
    title: str = ""
    rich_text: str = ""
    markdown: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    examples: List[ExampleItem] = Field(default_factory=list)
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class AudioTheoryBlockPayload(BaseModel):
    audio_url: str
    markdown: str


class ImageBlockPayload(BaseModel):
    image_url: Optional[str] = None
    explanation: str = ""
    keywords: List[str] = Field(default_factory=list)


class AudioBlockPayload(BaseModel):
    audio_url: str
    transcript: str
    translation: str


class FlashcardItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    word: str
    translation: str
    image_url: Optional[str] = Field(default=None, alias="image")
    audio_url: Optional[str] = None
    example_sentence: str = Field(default="", alias="example")
    pronunciation_enabled: bool = True


class FlashcardsBlockPayload(BaseModel):
    cards: List[FlashcardItem] = Field(default_factory=list)


class PronunciationItem(BaseModel):
    word: str
    audio_url: Optional[str] = None
    image_url: Optional[str] = None


class PronunciationBlockPayload(BaseModel):
    # legacy fields (kept optional for backward compatibility)
    phrase: Optional[str] = None
    sample_audio_url: Optional[str] = None
    expected_pronunciation: Optional[str] = None
    # new structure used by admin builder / student app
    items: List[PronunciationItem] = Field(default_factory=list)


class TheoryQuizBlockPayload(BaseModel):
    question: str = ""
    type: Literal["single", "multiple", "fill-in"] = "single"
    options: List[str] = Field(default_factory=list)
    correct_answer: List[str] | str | None = None
    explanation: str = ""


class AICheckPayload(BaseModel):
    enabled: bool = False
    endpoint: Optional[str] = None
    rubric: Optional[str] = None
    prompt: Optional[str] = None


class LessonTestQuestion(BaseModel):
    question: str
    type: Literal["single", "multiple", "fill-in", "audio_repeat", "open"] = "single"
    options: List[str] = Field(default_factory=list)
    correct_answer: List[str] | str | None = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    placeholder: Optional[str] = None
    explanation: Optional[str] = None
    ai_check: Optional[AICheckPayload] = None


class LessonTestBlockPayload(BaseModel):
    passing_score: int = 0
    questions: List[LessonTestQuestion] = Field(default_factory=list)


class AudioTaskPayload(BaseModel):
    audio_url: str
    transcript: str
    options: List[str] | None = None
    correct_answer: str
    answer_type: Literal["text", "multiple_choice"] = "multiple_choice"
    feedback: str | None = None


PAYLOAD_SCHEMAS: Dict[str, TypeAdapter] = {
    "video": TypeAdapter(VideoBlockPayload),
    "theory": TypeAdapter(TheoryBlockPayload),
    "audio_theory": TypeAdapter(AudioTheoryBlockPayload),
    "image": TypeAdapter(ImageBlockPayload),
    "audio": TypeAdapter(AudioBlockPayload),
    "flashcards": TypeAdapter(FlashcardsBlockPayload),
    "pronunciation": TypeAdapter(PronunciationBlockPayload),
    "theory_quiz": TypeAdapter(TheoryQuizBlockPayload),
    "lesson_test": TypeAdapter(LessonTestBlockPayload),
    "audio_task": TypeAdapter(AudioTaskPayload),
}


def validate_block_payload(block_type: str, payload: Dict[str, Any] | None) -> Dict[str, Any]:
    adapter = PAYLOAD_SCHEMAS.get(block_type)
    data = payload or {}
    if not adapter:
        return data
    model = adapter.validate_python(data)
    return model.model_dump()


class LessonBlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    lesson_id: int
    type: BlockType = Field(validation_alias="block_type")
    order: int
    content: dict


class NormalizedBlock(BaseModel):
    id: int
    order: int
    block_type: str
    type: str
    content: dict


class LessonBlockCreate(BaseModel):
    type: BlockType
    content: dict = Field(default_factory=dict)
    insert_after: Optional[int] = None


class LessonBlockUpdate(BaseModel):
    type: Optional[BlockType] = None
    content: Optional[dict] = None
    order: Optional[int] = None


class ReorderBlocks(BaseModel):
    order: List[int]


__all__ = [
    "LessonBlockOut",
    "NormalizedBlock",
    "BlockType",
    "validate_block_payload",
    "LessonBlockCreate",
    "LessonBlockUpdate",
    "ReorderBlocks",
    "VideoBlockPayload",
    "TheoryBlockPayload",
    "ImageBlockPayload",
    "AudioBlockPayload",
    "FlashcardsBlockPayload",
    "PronunciationBlockPayload",
    "TheoryQuizBlockPayload",
    "LessonTestBlockPayload",
    "AudioTaskPayload",
]
