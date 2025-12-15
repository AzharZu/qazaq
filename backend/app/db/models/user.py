from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base


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
    full_name = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    language = Column(String, nullable=True)
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


class UserStats(Base):
    __tablename__ = "user_stats"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    xp_total = Column(Integer, nullable=False, default=0)
    xp_today = Column(Integer, nullable=False, default=0)
    streak_days = Column(Integer, nullable=False, default=0)
    last_activity_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user: "User" = relationship("User")


class DailyGoal(Base):
    __tablename__ = "daily_goals"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_type = Column(String, nullable=False, default="light")
    target_value = Column(Integer, nullable=False, default=10)
    completed_today = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user: "User" = relationship("User")


class UserWord(Base):
    __tablename__ = "user_words"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    audio_url = Column(String, nullable=True)
    success_count = Column(Integer, nullable=False, default=0)
    fail_count = Column(Integer, nullable=False, default=0)
    next_review_at = Column(DateTime, nullable=True)

    user: "User" = relationship("User")


class PushToken(Base):
    __tablename__ = "push_tokens"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False, unique=True)
    device_type = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user: "User" = relationship("User")


__all__ = [
    "User",
    "PlacementTestResult",
    "UserStats",
    "DailyGoal",
    "UserWord",
    "PushToken",
]
