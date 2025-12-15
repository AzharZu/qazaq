from typing import List

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from ..base import Base


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


__all__ = ["Course"]
