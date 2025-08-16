from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    model_config = {"from_attributes": True}


class LeadCreate(BaseModel):
    name: str
    email: str | None = None
    notes: str | None = None


class TaskCreate(BaseModel):
    title: str
    lead_id: int | None = None


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    notes: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    lead_id: int | None = None


class LeadOut(BaseModel):
    id: int
    owner_id: int
    name: str
    email: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskOut(BaseModel):
    id: int
    owner_id: int
    lead_id: int | None = None
    title: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentRunRequest(BaseModel):
    lead_id: int | None = None
    context: str = ""


class AgentRunResponse(BaseModel):
    run_id: int
    status: str


class ArtifactOut(BaseModel):
    id: int
    kind: str
    content: str
    file_path: str | None = None
    status: str | None = None


class IdResponse(BaseModel):
    id: int
