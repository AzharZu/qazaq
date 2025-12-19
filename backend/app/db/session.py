from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..core.config import get_settings
from .base import Base

settings = get_settings()

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

db_url = settings.database_url
if "+asyncpg" in db_url:
    db_url = db_url.replace("+asyncpg", "+psycopg2")
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,  
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["SessionLocal", "engine", "Base"]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
