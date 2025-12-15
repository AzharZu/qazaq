from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base


class UserDictionary(Base):
    __tablename__ = "user_dictionary"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    example = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    added_at = Column(DateTime, server_default=func.now(), nullable=False)
    source_lesson_id = Column(Integer, nullable=True)
    source_block_id = Column(Integer, nullable=True)
    status = Column(String, nullable=True, default="new")
    last_practiced_at = Column(DateTime, nullable=True)
    last_practiced_at = Column(DateTime, nullable=True)

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
    status = Column(String, nullable=True, default="new")
    source_lesson_id = Column(Integer, nullable=True)
    source_block_id = Column(Integer, nullable=True)
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


class PronunciationResult(Base):
    __tablename__ = "pronunciation_results"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    word_id = Column(Integer, ForeignKey("vocabulary_words.id"), nullable=False, index=True)
    audio_url = Column(Text, nullable=False)
    score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user: "User" = relationship("User")
    word: "VocabularyWord" = relationship("VocabularyWord")


__all__ = ["UserDictionary", "VocabularyWord", "WordOfTheWeek", "PronunciationResult"]
