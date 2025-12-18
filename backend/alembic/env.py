import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).resolve().parents[1] / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.db import Base
from app.db import models  # noqa: F401

config = context.config

# ✅ Always override with environment variable
env_db_url = os.getenv("DATABASE_URL")

if not env_db_url:
    raise RuntimeError("DATABASE_URL is not set in environment!")

# Convert async URL to sync for alembic
if "+asyncpg" in env_db_url:
    env_db_url = env_db_url.replace("+asyncpg", "+psycopg2")

config.set_main_option("sqlalchemy.url", env_db_url)

# logging config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url = config.get_main_option("sqlalchemy.url")

    connectable = engine_from_config(
        {"sqlalchemy.url": url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()