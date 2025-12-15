import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["ADMIN_EMAILS"] = "[]"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.main import app  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db import models  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.core.config import get_settings  # noqa: E402


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_lessons.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    settings = get_settings()
    settings.upload_root = str(tmp_path / "uploads")
    Path(settings.upload_root).mkdir(parents=True, exist_ok=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def create_lesson_with_blocks(db):
    course = models.Course(slug="course", name="Course", description="Desc", audience="all")
    module = models.Module(name="Module", description="d", order=1, course=course)
    lesson = models.Lesson(module=module, title="Draft lesson", status="draft", order=1, language="kk")
    db.add_all([course, module, lesson])
    db.commit()
    db.refresh(lesson)

    b1 = models.LessonBlock(lesson_id=lesson.id, block_type="theory", content={"markdown": "one"}, order=2)
    b2 = models.LessonBlock(lesson_id=lesson.id, block_type="flashcards", content={"cards": []}, order=1)
    b3 = models.LessonBlock(lesson_id=lesson.id, block_type="pronunciation", content={"items": []}, order=3)
    db.add_all([b1, b2, b3])
    db.commit()
    db.refresh(b1)
    db.refresh(b2)
    db.refresh(b3)
    lesson.blocks_order = [b2.id, b1.id, b3.id]
    db.add(lesson)
    db.commit()
    return lesson, [b1, b2, b3]


def test_preview_returns_draft_blocks_sorted(client, db_session):
    lesson, blocks = create_lesson_with_blocks(db_session)

    resp = client.get(f"/api/lessons/{lesson.id}?preview=1")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["lesson"]["status"] == "draft"
    returned_ids = [b["id"] for b in payload["lesson"]["blocks"]]
    assert returned_ids == lesson.blocks_order  # respects explicit ordering
    assert db_session.query(models.UserProgress).count() == 0
    assert db_session.query(models.LessonProgress).count() == 0


def test_preview_required_for_draft_lessons(client, db_session):
    lesson, _ = create_lesson_with_blocks(db_session)

    resp = client.get(f"/api/lessons/{lesson.id}")
    assert resp.status_code in {401, 404}
