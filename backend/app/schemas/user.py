from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    age: int
    target: str
    daily_minutes: int = 10


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    age: int
    target: str
    daily_minutes: int
    level: Optional[str] = None
    role: Optional[str] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    is_admin: bool = False


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class PlacementResultCreate(BaseModel):
    user_id: Optional[int]
    level: str
    score: int


class PlacementResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    level: str
    score: int
    created_at: datetime


class SessionUser(BaseModel):
    id: int
    email: EmailStr
    role: Optional[str] = Field(default="user")


class AuthResponse(BaseModel):
    token: str
    user: UserOut


__all__ = [
    "UserCreate",
    "UserOut",
    "LoginPayload",
    "PlacementResultCreate",
    "PlacementResultOut",
    "SessionUser",
    "AuthResponse",
]
