from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from jose import jwt
from pydantic import BaseModel

# Minimal, standalone router. Server integration will import and include this.

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


JWT_SECRET = "dev-secret"  # should be configured by env when integrated
JWT_ALG = "HS256"


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    # Placeholder: accept any credentials in this scaffold
    now = datetime.now(UTC)
    exp = int((now + timedelta(hours=1)).timestamp())
    token = jwt.encode({"sub": req.email, "exp": exp}, JWT_SECRET, algorithm=JWT_ALG)
    return TokenResponse(access_token=token, expires_in=3600)


@router.post("/logout")
async def logout():
    return {"status": "ok"}




