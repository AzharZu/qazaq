import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# Get the absolute path to the project directory
PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_DB_PATH = PROJECT_DIR / "qazaq.db"


class Settings(BaseSettings):
    app_name: str = "Qazaq EdTech"
    secret_key: str = os.environ.get("SECRET_KEY", "devsecret")
    database_url: str = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
