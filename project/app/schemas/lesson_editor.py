from datetime import datetime
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

BlockType = Literal[
    "theory",
    "example",
    "pronunciation",
    "flashcards",
    "quiz",
    "image",
    "audio",
    "assignment",
    "mascot_tip",
    "dragdrop",  # legacy
    "story",  # legacy
]


class TheoryContent(BaseModel):
    heading: Optional[str] = None
    body: Optional[str] = None
    text: Optional[str] = None

    @model_validator(mode="after")
    def populate_body(cls, values):
        if values.body is None and values.text:
            values.body = values.text
        return values


class ExampleRow(BaseModel):
    kz: str = ""
    ru: str = ""


class ExampleContent(BaseModel):
    prompt: Optional[str] = None
    examples: List[ExampleRow] = Field(default_factory=list)


class PronunciationContent(BaseModel):
    words: List[str] = Field(default_factory=list)


class FlashcardsContent(BaseModel):
    flashcard_ids: List[int] = Field(default_factory=list)


class QuizContent(BaseModel):
    quiz_ids: List[int] = Field(default_factory=list)


class ImageContent(BaseModel):
    url: str = ""
    caption: Optional[str] = None


class AudioContent(BaseModel):
    url: str = ""
    transcript: Optional[str] = None


class AssignmentContent(BaseModel):
    prompt: str = ""
    rubric: Optional[str] = None
    max_score: Optional[int] = Field(default=None, ge=0)
    submission_type: str = Field(default="text", description="text, file, or audio")


class MascotTipContent(BaseModel):
    text: str = ""
    icon: Optional[str] = None


class LegacyContent(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: dict | None = None


class BlockCreateBase(BaseModel):
    insert_after: Optional[int] = Field(
        default=None,
        description="Optional block id; new block will be inserted after it.",
    )


class TheoryBlock(BlockCreateBase):
    type: Literal["theory"]
    content: TheoryContent


class ExampleBlock(BlockCreateBase):
    type: Literal["example"]
    content: ExampleContent


class PronunciationBlock(BlockCreateBase):
    type: Literal["pronunciation"]
    content: PronunciationContent


class FlashcardsBlock(BlockCreateBase):
    type: Literal["flashcards"]
    content: FlashcardsContent


class QuizBlock(BlockCreateBase):
    type: Literal["quiz"]
    content: QuizContent


class ImageBlock(BlockCreateBase):
    type: Literal["image"]
    content: ImageContent


class AudioBlock(BlockCreateBase):
    type: Literal["audio"]
    content: AudioContent


class AssignmentBlock(BlockCreateBase):
    type: Literal["assignment"]
    content: AssignmentContent


class MascotTipBlock(BlockCreateBase):
    type: Literal["mascot_tip"]
    content: MascotTipContent


class DragdropBlock(BlockCreateBase):
    type: Literal["dragdrop"]
    content: LegacyContent


class StoryBlock(BlockCreateBase):
    type: Literal["story"]
    content: LegacyContent


BlockCreate = Annotated[
    Union[
        TheoryBlock,
        ExampleBlock,
        PronunciationBlock,
        FlashcardsBlock,
        QuizBlock,
        ImageBlock,
        AudioBlock,
        AssignmentBlock,
        MascotTipBlock,
        DragdropBlock,
        StoryBlock,
    ],
    Field(discriminator="type"),
]


class BlockUpdate(BaseModel):
    type: Optional[BlockType] = None
    content: Optional[dict] = None
    order: Optional[int] = None


class BlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    lesson_id: int
    type: BlockType = Field(validation_alias="block_type")
    order: int
    content: dict
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(draft|published|archived)$")
    language: Optional[str] = None
    version: Optional[int] = None


class LessonSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    title: str
    status: Optional[str] = None
    language: Optional[str] = None
    order: Optional[int] = None


class LessonWithBlocksOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    module_id: int
    title: str
    description: Optional[str]
    order: Optional[int] = None
    status: Optional[str] = None
    language: Optional[str] = None
    version: Optional[int] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    blocks: List[BlockOut] = Field(default_factory=list)


class ReorderBlocks(BaseModel):
    order: List[int]

    @model_validator(mode="after")
    def ensure_unique(self):
        if len(self.order) != len(set(self.order)):
            raise ValueError("order must be unique")
        return self


BLOCK_CONTENT_MODELS = {
    "theory": TheoryContent,
    "example": ExampleContent,
    "pronunciation": PronunciationContent,
    "flashcards": FlashcardsContent,
    "quiz": QuizContent,
    "image": ImageContent,
    "audio": AudioContent,
    "assignment": AssignmentContent,
    "mascot_tip": MascotTipContent,
    "dragdrop": LegacyContent,
    "story": LegacyContent,
}


def validate_block_content(block_type: str, content: Optional[dict]) -> dict:
    model = BLOCK_CONTENT_MODELS.get(block_type)
    if not model:
        raise ValueError(f"Unsupported block type '{block_type}'")
    data = content or {}
    return model.model_validate(data).model_dump()
