import uuid

from fastapi import Request, Response

from sqlalchemy.exc import SQLAlchemyError

from ..db.session import SessionLocal
from ..db.models.user import User
from .security import get_user_id_from_request


async def assign_request_id(request: Request, call_next):
    request.state.request_id = uuid.uuid4().hex
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


async def enforce_utf8(request: Request, call_next):
    response: Response = await call_next(request)
    content_type = response.headers.get("content-type")
    if content_type and "application/json" in content_type and "charset" not in content_type.lower():
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response


async def load_current_user(request: Request, call_next):
    request.state.user = None
    user_id = get_user_id_from_request(request)
    if user_id:
        db = SessionLocal()
        try:
            user = db.get(User, user_id)
            request.state.user = user
        except SQLAlchemyError:
            # If migrations are not applied yet, skip attaching a user
            request.state.user = None
        finally:
            db.close()
    response = await call_next(request)
    return response
