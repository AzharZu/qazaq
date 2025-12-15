# Thin wrapper to ensure ``uvicorn app.main:app`` resolves the real app defined
# in /backend/app/main.py even if the working directory/reloader points at the
# nested /backend/backend tree. We prioritize the real backend path on sys.path
# and remove the nested shadow path so relative imports work correctly.
from app.main import app  # type: ignore  # noqa: F401

__all__ = ["app"]
