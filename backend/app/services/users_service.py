from sqlalchemy.orm import Session

from ..core.security import get_password_hash, verify_password
from ..db import models
from ..schemas.user import UserCreate


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user_in: UserCreate, level: str | None = None) -> models.User:
    user = models.User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        age=user_in.age,
        target=user_in.target,
        daily_minutes=user_in.daily_minutes,
        level=level,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


__all__ = ["get_user_by_email", "create_user", "verify_password"]
