import sys
from pathlib import Path
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure `app` package is on sys.path
os.environ["ADMIN_EMAILS"] = "[]"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.main import app
from app.db.base import Base
from app.db import models
from app.db.session import get_db
from app.core.security import get_password_hash
from app.core.config import get_settings


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_pronunciation.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    # Ensure uploads directory is isolated for tests
    settings = get_settings()
    settings.upload_root = str(tmp_path / "uploads")
    Path(settings.upload_root).mkdir(parents=True, exist_ok=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if Path(settings.upload_root).exists():
        for p in Path(settings.upload_root).rglob("*"):
            if p.is_file():
                p.unlink()


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


def create_user(db, email="user@example.com", password="secret", role="user"):
    user = models.User(
        email=email,
        hashed_password=get_password_hash(password),
        age=20,
        target="",
        daily_minutes=10,
        level="",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_course(db, slug="course-1"):
    course = models.Course(slug=slug, name="Course", description="desc", audience="adult")
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def create_word(db, user_id: int, course_id: int):
    word = models.VocabularyWord(
        user_id=user_id,
        course_id=course_id,
        word="kitap",
        translation="книга",
        learned=False,
    )
    db.add(word)
    db.commit()
    db.refresh(word)
    return word


def auth_token(client, email="user@example.com", password="secret"):
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return login.json()["token"]


def test_pronunciation_check_persists_result(client, db_session, tmp_path):
    user = create_user(db_session)
    course = create_course(db_session)
    word = create_word(db_session, user.id, course.id)
    token = auth_token(client)

    audio_bytes = b"fake audio data"
    resp = client.post(
        "/api/pronunciation/check",
        headers={"Authorization": f"Bearer {token}"},
        files={"audio": ("audio.wav", audio_bytes, "audio/wav")},
        data={"word_id": str(word.id)},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data and 0 <= data["score"] <= 1
    assert data["status"] in {"excellent", "good", "ok", "bad"}
    assert data["audio_url"].startswith("/uploads/pronunciation/")

    saved = (
        db_session.query(models.PronunciationResult)
        .filter(models.PronunciationResult.word_id == word.id, models.PronunciationResult.user_id == user.id)
        .first()
    )
    assert saved is not None
    assert saved.score == data["score"]
    # File exists on disk
    settings = get_settings()
    audio_path = Path(settings.upload_root) / "pronunciation" / Path(data["audio_url"]).name
    assert audio_path.exists() is True
