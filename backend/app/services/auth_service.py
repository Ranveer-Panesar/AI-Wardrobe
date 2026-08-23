"""
DB read/write operations for auth. Kept separate from app/routers/auth.py
so the route handlers stay focused on request/response shape and this file
stays focused on "how do we actually query/create a user."

NOTE: uses the `User` model from app.models.user. If the schema changes
there (it's the DB-owner's file), these functions may need small updates —
keep an eye on this file in review when that model changes.
"""
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_phone(db: Session, phone: str) -> User | None:
    return db.query(User).filter(User.phone == phone).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, phone: str, password_hash: str) -> User:
    user = User(email=email, phone=phone, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
