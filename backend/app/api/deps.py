from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..core.security import get_user_id_from_request
from ..core.config import get_settings
from ..db import get_db
from ..db.models import User


def current_db(request: Request, db: Session = Depends(get_db)) -> Session:
    request.state.db = db
    return db


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    allow_anonymous: bool = False,
) -> User | None:
    if getattr(request.state, "user", None):
        return request.state.user

    user_id = get_user_id_from_request(request)
    if user_id:
        user = db.get(User, user_id)
        request.state.user = user
        if user:
            return user

    if allow_anonymous:
        return None
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db=db, allow_anonymous=False)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = require_user(request, db=db)
    if request.method == "OPTIONS":
        return user
    settings = get_settings()
    admin_emails = set(settings.admin_emails or [])
    if (user.role or "").lower() == "admin" or (user.email or "").lower() in admin_emails:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


def get_user_or_none(request: Request, db: Session = Depends(get_db)) -> User | None:
    return get_current_user(request, db=db, allow_anonymous=True)


__all__ = ["current_db", "get_current_user", "require_user", "require_admin", "get_user_or_none"]
