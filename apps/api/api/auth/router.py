"""Authentication endpoints (AGENTS.md §29: auth)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from security import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = auth.ensure_demo_user(db)
    if user is None:
        raise HTTPException(status_code=500, detail="Demo user seed failed")
    if form.username != user.username or not auth.verify_password(
        form.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = auth.create_access_token(subject=user.username, user_id=user.id)
    return TokenResponse(
        access_token=token, user_id=user.id, username=user.username
    )


@router.post("/login/json", response_model=TokenResponse)
def login_json(
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = auth.ensure_demo_user(db)
    if user is None:
        raise HTTPException(status_code=500, detail="Demo user seed failed")
    if body.username != user.username or not auth.verify_password(
        body.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = auth.create_access_token(subject=user.username, user_id=user.id)
    return TokenResponse(
        access_token=token, user_id=user.id, username=user.username
    )


@router.get("/me")
def me(current=Depends(auth.get_current_user)) -> dict:
    return {"id": current.id, "username": current.username}
