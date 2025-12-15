from typing import List

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..base import Base


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


__all__ = ["Module"]
