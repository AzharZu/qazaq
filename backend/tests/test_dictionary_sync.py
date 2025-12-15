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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dictionary_sync.db"
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


def create_user(db, email="user@example.com"):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("secret"),
        age=30,
        target="",
        daily_minutes=10,
        level="",
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(client, email="user@example.com", password="secret"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def bootstrap_lesson(db, slug="course-1", title="Lesson 1", words=None):
    words = words or [
        {"word": "Күн", "translation": "День"},
        {"word": "Ай", "translation": "Луна"},
    ]
    course = models.Course(slug=slug, name="Course", description="", audience="")
    module = models.Module(name="M1", description="", order=1, course=course)
    lesson = models.Lesson(module=module, title=title, status="published", order=1, language="kk", blocks_order=[])
    db.add_all([course, module, lesson])
    db.commit()
    db.refresh(lesson)
    block = models.LessonBlock(lesson_id=lesson.id, block_type="flashcards", content={"cards": words}, order=1)
    db.add(block)
    db.commit()
    db.refresh(block)
    lesson.blocks_order = [block.id]
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson, block


def test_dictionary_sync_on_lesson_fetch(client, db_session):
    create_user(db_session)
    headers = auth_headers(client)
    lesson, _ = bootstrap_lesson(db_session, title="Lesson sync")

    resp = client.get(f"/api/lessons/{lesson.id}", headers=headers)
    assert resp.status_code == 200
    vocab = db_session.query(models.VocabularyWord).filter(models.VocabularyWord.user_id == 1).all()
    assert len(vocab) == 2
    for w in vocab:
        assert w.source_lesson_id == lesson.id
        assert w.status in {"new", None} or w.status == "new"

    # second fetch should not duplicate
    resp = client.get(f"/api/lessons/{lesson.id}", headers=headers)
    assert resp.status_code == 200
    vocab_again = db_session.query(models.VocabularyWord).filter(models.VocabularyWord.user_id == 1).all()
    assert len(vocab_again) == 2


def test_dictionary_filter_by_lesson(client, db_session):
    create_user(db_session, email="user2@example.com")
    headers = auth_headers(client, email="user2@example.com")
    lesson1, _ = bootstrap_lesson(db_session, slug="c1", title="Lesson A", words=[{"word": "Су", "translation": "Вода"}])
    lesson2, _ = bootstrap_lesson(db_session, slug="c1b", title="Lesson B", words=[{"word": "Жел", "translation": "Ветер"}])

    client.get(f"/api/lessons/{lesson1.id}", headers=headers)
    client.get(f"/api/lessons/{lesson2.id}", headers=headers)

    resp = client.get("/api/dictionary", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    filtered = client.get(f"/api/dictionary?lessonId={lesson1.id}", headers=headers)
    assert filtered.status_code == 200
    data = filtered.json()
    assert len(data) == 1
    assert data[0]["source_lesson_id"] == lesson1.id


def test_submit_result_updates_status_and_last_practiced(client, db_session):
    create_user(db_session, email="user3@example.com")
    headers = auth_headers(client, email="user3@example.com")
    lesson, _ = bootstrap_lesson(db_session, slug="c3", title="Lesson Game", words=[{"word": "Апа", "translation": "Мама"}])
    client.get(f"/api/lessons/{lesson.id}", headers=headers)
    word = db_session.query(models.VocabularyWord).filter(models.VocabularyWord.user_id == 1).first()
    assert word.status == "new"
    resp = client.post(f"/api/dictionary/{word.id}/result", headers=headers, json={"mode": "write", "correct": True})
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["status"] in {"learning", "learned"}
    assert updated["last_practiced_at"] is not None
