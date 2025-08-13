from __future__ import annotations

from typing import Annotated

from app.core.security import create_access_token
from app.db import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas import LoginRequest, RegisterRequest, UserOut
from fastapi import APIRouter, Depends, HTTPException, status
from app.security.deps import require_scopes
from app.security.scopes import ADMIN_USERS
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/users", tags=["users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> UserOut:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid credentials")
    token = create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserOut,
)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
