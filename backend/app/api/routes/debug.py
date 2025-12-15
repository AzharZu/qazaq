from fastapi import APIRouter, Depends, Request

from ...api import deps
from ...db.models import User

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/cookies")
def debug_cookies(request: Request):
    return {"cookies": request.cookies}


@router.get("/user")
def debug_user(user: User = Depends(deps.require_user)):
    return {"id": user.id, "email": user.email}
