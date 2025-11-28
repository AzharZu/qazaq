from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from . import routers  # noqa: F401
from .routers import admin as admin_router
from .sessions import get_current_user_from_request

settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    https_only=False,  # allow http on localhost
    same_site="lax",
    session_cookie="qazaq_session",
    max_age=60 * 60 * 24,  # 1 day
)

BASE_DIR = Path(__file__).parent

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

app.include_router(routers.auth.router)
app.include_router(routers.autochecker.router)
app.include_router(routers.placement.router)
app.include_router(routers.courses.router)
app.include_router(routers.modules.router)
app.include_router(routers.lessons.router)
app.include_router(routers.users.router)
app.include_router(routers.dictionary.router)
app.include_router(admin_router.router, prefix="/admin", tags=["admin"])


@app.middleware("http")
async def load_current_user(request, call_next):
    request.state.user = None
    user = get_current_user_from_request(request)
    if user:
        request.state.user = user
    response = await call_next(request)
    return response
