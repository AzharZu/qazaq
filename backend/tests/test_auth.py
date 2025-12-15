import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure `app` package is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.main import app
from app.db.base import Base
from app.db import models
from app.db.session import get_db
from app.core.security import get_password_hash


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
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


def test_login_success(client, db_session):
    create_user(db_session, password="pass123")
    resp = client.post("/api/auth/login", json={"email": "user@example.com", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "user@example.com"


def test_login_failure(client, db_session):
    create_user(db_session, password="pass123")
    resp = client.post("/api/auth/login", json={"email": "user@example.com", "password": "wrong"})
    assert resp.status_code == 400


def test_me_unauthorized(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_success(client, db_session):
    create_user(db_session, password="pass123")
    login = client.post("/api/auth/login", json={"email": "user@example.com", "password": "pass123"})
    token = login.json()["token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@example.com"
