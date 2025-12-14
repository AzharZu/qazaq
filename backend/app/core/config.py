from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from sqlalchemy.engine.url import URL, make_url


DEFAULT_DB_URL = "postgresql+asyncpg://qazaq_user:qazaq_pass@postgres:5432/qazaq_db"


class Settings(BaseSettings):
    app_name: str = "Qazaq EdTech"
    secret_key: str = "change-me"
    database_url: str = DEFAULT_DB_URL
    database_sync_url: str | None = None
    allowed_origins: list[str] = Field(default_factory=list)
    allowed_origin_regex: str | None = None
    gemini_api_key: str | None = None
    google_speech_api_key: str | None = None
    upload_root: str | None = None
    cdn_base_url: str | None = None
    session_cookie: str = "session"
    admin_emails: list[str] = Field(default_factory=list)

    class Config:
        # Use absolute path to the backend/.env to avoid issues when the working
        # directory is the nested backend/backend during reload.
        env_file = str(Path(__file__).resolve().parents[2] / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def _parse_origins(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned.startswith("[") and cleaned.endswith("]"):
                try:
                    import json

                    parsed = json.loads(cleaned)
                    if isinstance(parsed, list):
                        return [str(v) for v in parsed]
                except Exception:
                    pass
            return [v.strip() for v in cleaned.split(",") if v.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(v) for v in value]
        return []

    @field_validator("admin_emails", mode="before")
    @classmethod
    def _parse_admin_emails(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [v.strip().lower() for v in value.split(",") if v.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(v).strip().lower() for v in value if str(v).strip()]
        return []


def _normalize_db_url(raw: str) -> tuple[str, str]:
    """Return (original_url, sync_url) ensuring sync_url uses a sync driver."""
    raw = raw or DEFAULT_DB_URL
    url = make_url(raw)
    driver = url.drivername or ""
    sync_url: URL = url
    if "+asyncpg" in driver:
        sync_url = url.set(drivername=driver.replace("+asyncpg", "+psycopg2"))
    elif driver == "postgresql":
        sync_url = url.set(drivername="postgresql+psycopg2")
    # Use render_as_string to avoid password masking ("***") in str(url)
    original = url.render_as_string(hide_password=False)
    sync = sync_url.render_as_string(hide_password=False)
    return original, sync


def _normalize_upload_root(value: str | None, project_root: Path) -> str:
    if not value:
        # In Docker, use /app/uploads; locally use project_root/uploads
        if Path("/app").exists() and Path("/app/uploads").exists():
            value = "/app/uploads"
        else:
            value = str(project_root / "uploads")
    path = Path(value)
    if not path.is_absolute():
        path = (project_root / value).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _normalize_cdn_base(value: str | None) -> str:
    base = (value or "/uploads").strip() or "/uploads"
    if not base.startswith("/"):
        base = f"/{base}"
    return base.rstrip("/") or "/uploads"


@lru_cache()
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[3]
    settings = Settings()
    original_url, sync_url = _normalize_db_url(settings.database_url)
    settings.database_url = original_url
    settings.database_sync_url = sync_url
    settings.upload_root = _normalize_upload_root(settings.upload_root, project_root)
    settings.cdn_base_url = _normalize_cdn_base(settings.cdn_base_url)
    if not settings.allowed_origins:
        settings.allowed_origins = [
            "http://localhost",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    if not settings.allowed_origin_regex:
        # Wide dev default so new preview ports do not break CORS; override via env if needed.
        settings.allowed_origin_regex = r".*"
    return settings
