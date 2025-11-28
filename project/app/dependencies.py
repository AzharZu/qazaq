from fastapi import Depends, HTTPException, Request, status

from . import models
from .sessions import get_current_user_from_request


def _redirect_flag() -> bool:
    return True


def get_current_user(request: Request, redirect_on_fail: bool = Depends(_redirect_flag)) -> models.User | None:
    user = get_current_user_from_request(request)
    if user:
        request.state.user = user
        return user

    request.state.user = None
    if redirect_on_fail:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
            detail="Not authenticated",
        )
    return None


def require_admin(request: Request) -> models.User:
    user = get_current_user(request)
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    request.state.user = user
    return user


def require_user(request: Request) -> models.User:
    return get_current_user(request)
