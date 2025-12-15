from sqlalchemy import Column, Integer, ForeignKey, JSON, String, DateTime, func
from sqlalchemy.orm import relationship

from ..base import Base


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="in_progress")
    completed_blocks = Column(JSON, nullable=True)
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    finished_at = Column(DateTime, nullable=True)

    user = relationship("User")
    lesson = relationship("Lesson")


class UserCourseProgress(Base):
    __tablename__ = "user_course_progress"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    percent = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    course = relationship("Course")


__all__ = ["UserLessonProgress", "UserCourseProgress"]
