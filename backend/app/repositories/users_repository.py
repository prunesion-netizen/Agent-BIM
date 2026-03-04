"""
users_repository.py — CRUD pentru tabela users.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.sql_models import UserModel


def create_user(
    db: Session,
    email: str,
    username: str,
    hashed_password: str,
    role: str = "viewer",
) -> UserModel:
    """Creează un utilizator nou."""
    user = UserModel(
        email=email,
        username=username,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    """Caută un utilizator după email."""
    return db.query(UserModel).filter(UserModel.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    """Caută un utilizator după username."""
    return db.query(UserModel).filter(UserModel.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[UserModel]:
    """Caută un utilizator după ID."""
    return db.query(UserModel).filter(UserModel.id == user_id).first()
