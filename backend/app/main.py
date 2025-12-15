from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, ORJSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from .api.routes import (
    auth,
    autochecker,
    blocks,
    certificates,
    courses,
    debug,
    dictionary,
    lessons,
    admin_lessons,
    admin_blocks,
    upload,
    modules,
    audio_task,
    placement,
    placement_admin,
    pronunciation,
    progress,
    users,
    level_test,
    vocabulary,
)
from .core.config import get_settings
from .core.middleware import enforce_utf8, load_current_user
from .db.session import SessionLocal

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    default_response_class=ORJSONResponse,
)

# Build explicit origin list, ensuring student dev port (3002) is included.
cors_origins = settings.allowed_origins or []
if "http://localhost:3002" not in cors_origins:
    cors_origins.append("http://localhost:3002")
if "http://127.0.0.1:3002" not in cors_origins:
    cors_origins.append("http://127.0.0.1:3002")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    https_only=False,
    same_site="lax",
    session_cookie="qazaq_state",
    max_age=86400 * 30,  # 30 days
)
app.middleware("http")(enforce_utf8)
app.middleware("http")(load_current_user)


def _ensure_enum_values():
    if "postgres" not in settings.database_url:
        return
    try:
        with SessionLocal() as db:
            # Skip if enum type was never created (older DBs store block_type as varchar).
            exists = db.execute(text("SELECT 1 FROM pg_type WHERE typname = 'block_type_enum'")).scalar()
            if not exists:
                return
            db.execute(
                text(
                    """
                    DO $$ BEGIN
                      IF NOT EXISTS (
                        SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid
                        WHERE t.typname = 'block_type_enum' AND e.enumlabel = 'audio_task'
                      ) THEN
                        ALTER TYPE block_type_enum ADD VALUE 'audio_task';
                      END IF;
                    END $$;
                    """
                )
            )
            db.commit()
    except Exception:
        # ENUM type doesn't exist yet, migrations haven't run
        pass


_ensure_enum_values()

# Mount static for compiled SPA assets
ROOT_DIR = Path(__file__).resolve().parents[2]
STUDENT_DIST = ROOT_DIR / "student-spa" / "dist"
ADMIN_DIST = ROOT_DIR / "admin-spa" / "dist"
BACKEND_STATIC = Path(__file__).resolve().parent / "static"

app.mount("/app/assets", StaticFiles(directory=str(STUDENT_DIST / "assets"), check_dir=False), name="student-assets")
app.mount("/admin/assets", StaticFiles(directory=str(ADMIN_DIST / "assets"), check_dir=False), name="admin-assets")
app.mount("/static", StaticFiles(directory=str(BACKEND_STATIC), check_dir=False), name="static")

# API routers
app.include_router(auth.router)
app.include_router(autochecker.router)
app.include_router(level_test.router)
app.include_router(courses.router)
app.include_router(modules.router)
app.include_router(lessons.router)
app.include_router(admin_lessons.router)
app.include_router(admin_blocks.router)
app.include_router(blocks.router)
app.include_router(upload.router)
app.include_router(upload.admin_router)
app.include_router(progress.router)
app.include_router(audio_task.router)
app.include_router(placement.router)
app.include_router(placement_admin.router)
app.include_router(pronunciation.router)
app.include_router(dictionary.router)
app.include_router(certificates.router)
app.include_router(vocabulary.router)
app.include_router(users.router)
app.include_router(debug.router)


def _spa_response(dist_dir: Path) -> FileResponse:
    index_file = dist_dir / "index.html"
    if not index_file.exists():
        raise HTTPException(
            status_code=503,
            detail=f"SPA build not found at {index_file}. Run the build and try again.",
        )
    return FileResponse(index_file)


@app.get("/app", include_in_schema=False)
@app.get("/app/{full_path:path}", include_in_schema=False)
async def serve_student_spa(full_path: str | None = None):
    return _spa_response(STUDENT_DIST)


@app.get("/admin", include_in_schema=False)
@app.get("/admin/{full_path:path}", include_in_schema=False)
async def serve_admin_spa(full_path: str | None = None):
    return _spa_response(ADMIN_DIST)


@app.get("/", include_in_schema=False)
async def root_redirect():
    if STUDENT_DIST.exists():
        return FileResponse(STUDENT_DIST / "index.html")
    return PlainTextResponse("Qazaq API is running. Build the SPA to serve /app.", media_type="text/plain")
