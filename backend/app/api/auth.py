"""
auth.py — Router API pentru autentificare: register, login, refresh, me.

POST /api/auth/register — creează cont nou
POST /api/auth/login    — autentificare, returnează access + refresh token
POST /api/auth/refresh  — reînnoiește access token
GET  /api/auth/me       — returnează utilizatorul curent
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.repositories.users_repository import (
    create_user,
    get_user_by_email,
    get_user_by_username,
)
from app.schemas.auth import (
    TokenRefreshRequest,
    TokenResponse,
    UserLogin,
    UserRead,
    UserRegister,
)
from app.schemas.converters import user_model_to_read
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def api_register(data: UserRegister, db: Session = Depends(get_db)):
    """Creează un cont nou și returnează tokens."""
    if get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un cont cu acest email există deja.",
        )
    if get_user_by_username(db, data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username-ul este deja utilizat.",
        )
    if len(data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parola trebuie să aibă minim 6 caractere.",
        )

    hashed = hash_password(data.password)
    user = create_user(db, data.email, data.username, hashed)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=user_model_to_read(user),
    )


@router.post("/login", response_model=TokenResponse)
def api_login(data: UserLogin, db: Session = Depends(get_db)):
    """Autentifică un utilizator și returnează tokens."""
    user = get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email sau parolă incorectă.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contul este dezactivat.",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=user_model_to_read(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def api_refresh(data: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Reînnoiește access token-ul folosind refresh token."""
    user_id = decode_token(data.refresh_token, expected_type="refresh")
    from app.repositories.users_repository import get_user_by_id

    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizator inexistent sau dezactivat.",
        )

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=user_model_to_read(user),
    )


@router.get("/me", response_model=UserRead)
def api_me(current_user: UserModel = Depends(get_current_user)):
    """Returnează datele utilizatorului curent."""
    return user_model_to_read(current_user)
