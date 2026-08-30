"""JWT authentication (AGENTS.md §29, §33).

Uses bcrypt directly for password hashing (avoids passlib/bcrypt version
conflicts) and PyJWT for tokens. All secrets come from settings/env.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from config.settings import settings
from db.models import User
from db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── password helpers ─────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str | int, user_id: int | None = None) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(subject), "exp": expire}
    if user_id is not None:
        payload["uid"] = user_id
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# ── data access ──────────────────────────────────────────────
def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


def ensure_demo_user(db: Session) -> User:
    """Seed the demo admin user (safe default for the MVP)."""
    user = db.query(User).filter(User.username == settings.demo_username).first()
    if user is None:
        user = User(
            username=settings.demo_username,
            password_hash=hash_password(settings.demo_password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ── FastAPI dependencies ─────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username: str = payload.get("sub", "")
        if not username:
            raise credentials_exception
    except jwt.PyJWTError as exc:
        raise credentials_exception from exc
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
