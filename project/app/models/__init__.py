from datetime import datetime
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class User(Base):
    __tablename__ = "users"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    target = Column(String, nullable=False)  # school / general / business
    daily_minutes = Column(Integer, nullable=False, default=10)
    level = Column(String, nullable=True)
    role = Column(String, nullable=False, default="user")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    placements: List["PlacementTestResult"] = relationship(
        "PlacementTestResult", back_populates="user", cascade="all, delete-orphan"
    )
    progresses: List["UserProgress"] = relationship(
        "UserProgress", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def is_admin(self) -> bool:
        return (self.role or "").lower() == "admin"


class PlacementTestResult(Base):
    __tablename__ = "placement_results"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    level = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    answers = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user: "User" = relationship("User", back_populates="placements")


class Course(Base):
    __tablename__ = "courses"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    audience = Column(String, nullable=False)  # kids / adult / gov

    modules: List["Module"] = relationship(
        "Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order"
    )


class Module(Base):
    __tablename__ = "modules"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)

    course: "Course" = relationship("Course", back_populates="modules")
    lessons: List["Lesson"] = relationship(
        "Lesson", back_populates="module", cascade="all, delete-orphan", order_by="Lesson.order"
    )


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
    age_group = Column(String, nullable=True)  # kids / adult / gov
    order = Column(Integer, nullable=False, default=1)

    module: "Module" = relationship("Module", back_populates="lessons")
    blocks: List["LessonBlock"] = relationship(
        "LessonBlock", back_populates="lesson", cascade="all, delete-orphan", order_by="LessonBlock.order"
    )
    flashcards: List["Flashcard"] = relationship(
        "Flashcard", back_populates="lesson", cascade="all, delete-orphan"
    )
    quizzes: List["Quiz"] = relationship(
        "Quiz", back_populates="lesson", cascade="all, delete-orphan"
    )


class LessonBlock(Base):
    __tablename__ = "lesson_blocks"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    block_type = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    order = Column(Integer, nullable=False, default=1)

    lesson: "Lesson" = relationship("Lesson", back_populates="blocks")


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
    last_opened_at = Column(DateTime, default=datetime.utcnow, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_progress_user_lesson"),)

    user: "User" = relationship("User", back_populates="progresses")
    lesson: "Lesson" = relationship("Lesson")


class UserDictionary(Base):
    __tablename__ = "user_dictionary"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    example = Column(Text, nullable=True)
    added_at = Column(DateTime, server_default=func.now(), nullable=False)

    user: "User" = relationship("User")
    course: "Course" = relationship("Course")


class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    definition = Column(Text, nullable=True)
    example_sentence = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    learned = Column(Boolean, nullable=False, default=False)
    repeat_streak = Column(Integer, nullable=False, default=0)
    mc_streak = Column(Integer, nullable=False, default=0)
    write_streak = Column(Integer, nullable=False, default=0)
    correct_attempts = Column(Integer, nullable=False, default=0)
    wrong_attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user: "User" = relationship("User")
    course: "Course" = relationship("Course")


class WordOfTheWeek(Base):
    __tablename__ = "word_of_the_week"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    word_id = Column(Integer, ForeignKey("vocabulary_words.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    stats_views = Column(Integer, nullable=False, default=0)
    stats_correct_answers = Column(Integer, nullable=False, default=0)

    word: "VocabularyWord" = relationship("VocabularyWord")


__all__ = [
    "User",
    "PlacementTestResult",
    "Course",
    "Module",
    "Lesson",
    "LessonBlock",
    "Flashcard",
    "Quiz",
    "UserProgress",
    "UserDictionary",
    "VocabularyWord",
    "WordOfTheWeek",
]
