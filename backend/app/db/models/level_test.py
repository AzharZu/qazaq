from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..base import Base


class LevelTestQuestion(Base):
    __tablename__ = "level_test_questions"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    example = Column(Text, nullable=True)
    correct_index = Column(Integer, nullable=False, default=0)

    options = relationship("LevelTestOption", back_populates="question", cascade="all, delete-orphan")


class LevelTestOption(Base):
    __tablename__ = "level_test_options"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("level_test_questions.id"), nullable=False, index=True)
    text = Column(String, nullable=False)
    order = Column(Integer, nullable=False, default=0)

    question = relationship("LevelTestQuestion", back_populates="options")


__all__ = ["LevelTestQuestion", "LevelTestOption"]
