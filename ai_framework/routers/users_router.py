from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_framework.models_extra import User
from core.db import get_session

router = APIRouter(prefix="/api/users", tags=["users"])


class UserIn(BaseModel):
    email: str
    name: str | None = None
    role: str | None = None


class UserOut(BaseModel):
    id: int
    email: str
    name: str | None
    role: str | None
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[UserOut])
async def list_users():
    with get_session() as session:  # type: ignore
        records = session.query(User).all()
        return [UserOut.model_validate(r) for r in records]


@router.post("/", response_model=UserOut)
async def create_user(body: UserIn):
    with get_session() as session:  # type: ignore
        if session.query(User).filter_by(email=body.email).first():
            raise HTTPException(status_code=400, detail="Email already exists")
        u = User(email=body.email, name=body.name, role=body.role)
        session.add(u)
        session.commit()
        session.refresh(u)
        return UserOut.model_validate(u)




