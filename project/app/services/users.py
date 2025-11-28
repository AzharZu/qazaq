from sqlalchemy.orm import Session
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from passlib.hash import pbkdf2_sha256

from .. import models
from ..schemas import UserCreate

# Use pbkdf2_sha256 to avoid bcrypt 72-byte limits/backends issues.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False


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
