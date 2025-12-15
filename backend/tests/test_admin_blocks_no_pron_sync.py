import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.main import app  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db import models  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin_blocks.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
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


def create_admin(db, email="admin@example.com"):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("secret"),
        age=30,
        target="",
        daily_minutes=10,
        level="",
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(client, email="admin@example.com", password="secret"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def bootstrap_lesson(db):
    course = models.Course(slug="c1", name="Course", description="", audience="")
    module = models.Module(name="M1", description="", order=1, course=course)
    lesson = models.Lesson(module=module, title="L1", status="draft", order=1, language="kk", blocks_order=[])
    db.add_all([course, module, lesson])
    db.commit()
    db.refresh(lesson)
    block = models.LessonBlock(lesson_id=lesson.id, block_type="pronunciation", content={"items": []}, order=1)
    db.add(block)
    db.commit()
    db.refresh(block)
    return lesson, block


def test_patch_pronunciation_block_does_not_touch_missing_table(client, db_session):
    create_admin(db_session)
    headers = auth_headers(client)
    lesson, block = bootstrap_lesson(db_session)
    resp = client.patch(f"/api/admin/lessons/blocks/{block.id}", headers=headers, json={"content": {"items": []}})
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "pronunciation"


def test_reorder_canonical_no_conflict(client, db_session):
    create_admin(db_session)
    headers = auth_headers(client)
    lesson, block = bootstrap_lesson(db_session)
    # add task + flashcards blocks
    fc = models.LessonBlock(lesson_id=lesson.id, block_type="flashcards", content={"cards": [{"word": "a", "translation": "b"}]}, order=2)
    task = models.LessonBlock(lesson_id=lesson.id, block_type="quiz", content={"question": "q", "options": ["a"], "correct_answer": ["a"]}, order=3)
    db_session.add_all([fc, task])
    db_session.commit()
    db_session.refresh(fc)
    db_session.refresh(task)
    payload = {"order": [task.id, fc.id]}
    resp = client.post(f"/api/admin/lessons/{lesson.id}/blocks/reorder", headers=headers, json=payload)
    assert resp.status_code in {200, 204}
    # Ensure only reorderable blocks swapped
    updated = db_session.get(models.LessonBlock, task.id)
    assert updated.order == 1 or updated.order == 2
