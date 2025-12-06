#!/usr/bin/env python3
"""Initialize the database with all tables."""

from project.app.database import Base, engine
from project.app.models import (
    User,
    PlacementTestResult,
    Course,
    Module,
    Lesson,
    LessonBlock,
    Flashcard,
    Quiz,
    UserProgress,
    UserDictionary,
    VocabularyWord,
    WordOfTheWeek,
)

def init_db():
    """Create all tables in the database."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")

if __name__ == "__main__":
    init_db()
