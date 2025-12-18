from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, JSON, UniqueConstraint, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base

BLOCK_TYPE_CHOICES = (
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
    "free_writing",
    # Compatibility/legacy buckets
    "quiz",
    "example",
    "assignment",
    "mascot_tip",
    "dragdrop",
    "story",
)


class LessonBlock(Base):
    __tablename__ = "lesson_blocks"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    block_type = Column(Enum(*BLOCK_TYPE_CHOICES, name="block_type_enum"), nullable=False)
    content = Column(JSON, nullable=False)
    # Unified payload for new-style blocks
    data = Column(JSON, nullable=True)
    order = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("lesson_id", "order", name="uq_lesson_blocks_lesson_order"),)

    lesson: "Lesson" = relationship("Lesson", back_populates="blocks")

    @property
    def type(self) -> str:
        return self.block_type

    @type.setter
    def type(self, value: str) -> None:
        self.block_type = value

    @property
    def payload(self) -> dict:
        return (self.data or self.content or {}) if isinstance(self.data or self.content, dict) else {}


class AudioTask(Base):
    __tablename__ = "audio_tasks"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("lesson_blocks.id"), nullable=False, unique=True)
    audio_path = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    transcript = Column(String, nullable=True)
    options = Column(JSON, nullable=True)
    correct_answer = Column(String, nullable=True)
    answer_type = Column(String, nullable=False, default="text")  # text | multiple_choice
    feedback = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    block: "LessonBlock" = relationship("LessonBlock", backref="audio_task", uselist=False)


class PronunciationBlock(Base):
    __tablename__ = "pronunciation_blocks"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("lesson_blocks.id"), nullable=False, unique=True)
    reference_audio_url = Column(String, nullable=True)
    reference_text = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    block: "LessonBlock" = relationship("LessonBlock", backref="pronunciation_block", uselist=False)


__all__ = ["LessonBlock", "BLOCK_TYPE_CHOICES", "AudioTask", "PronunciationBlock"]
