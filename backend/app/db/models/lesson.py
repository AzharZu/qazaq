from datetime import datetime
from typing import List

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base
from .block import LessonBlock, BLOCK_TYPE_CHOICES


class Lesson(Base):
    __tablename__ = "lessons"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    lesson_type = Column(String, nullable=True)
    estimated_time = Column(Integer, nullable=True)
    difficulty = Column(String, nullable=True)
    age_group = Column(String, nullable=True)
    order = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="draft")
    language = Column(String, nullable=False, default="kk")
    version = Column(Integer, nullable=False, default=1)
    blocks_order = Column(JSON, nullable=True, default=list)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    module: "Module" = relationship("Module", back_populates="lessons")
    blocks: List["LessonBlock"] = relationship(
        "LessonBlock", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonBlock.order"
    )
    flashcards: List["Flashcard"] = relationship("Flashcard", back_populates="lesson", cascade="all, delete-orphan")
    pronunciations: List["PronunciationItem"] = relationship(
        "PronunciationItem", back_populates="lesson", cascade="all, delete-orphan", order_by="PronunciationItem.order"
    )
    quizzes: List["Quiz"] = relationship("Quiz", back_populates="lesson", cascade="all, delete-orphan")

class Flashcard(Base):
    __tablename__ = "flashcards"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    front = Column(String, nullable=False)
    back = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    age_group = Column(String, nullable=True)
    order = Column(Integer, nullable=False, default=1)

    lesson: "Lesson" = relationship("Lesson", back_populates="flashcards")


class PronunciationItem(Base):
    __tablename__ = "pronunciation_items"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=True)
    example = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    order = Column(Integer, nullable=False, default=1)

    lesson: "Lesson" = relationship("Lesson", back_populates="pronunciations")


class Quiz(Base):
    __tablename__ = "quizzes"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    correct_option = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    age_group = Column(String, nullable=True)
    order = Column(Integer, nullable=False, default=1)

    lesson: "Lesson" = relationship("Lesson", back_populates="quizzes")


class UserProgress(Base):
    __tablename__ = "user_progress"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    status = Column(String, nullable=False, default="done")
    time_spent = Column(Integer, nullable=False, default=0)
    completed_at = Column(DateTime, nullable=True)
    last_opened_at = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_progress_user_lesson"),)

    user: "User" = relationship("User", back_populates="progresses")
    lesson: "Lesson" = relationship("Lesson")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False, index=True)
    completed = Column(Boolean, nullable=False, default=False)
    score = Column(Integer, nullable=True)
    time_spent = Column(Integer, nullable=False, default=0)
    details = Column(JSON, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_lesson_progress_user_lesson"),)

    user: "User" = relationship("User")
    lesson: "Lesson" = relationship("Lesson")


__all__ = [
    "Lesson",
    "LessonBlock",
    "Flashcard",
    "Quiz",
    "UserProgress",
    "LessonProgress",
    "BLOCK_TYPE_CHOICES",
    "PronunciationItem",
]
