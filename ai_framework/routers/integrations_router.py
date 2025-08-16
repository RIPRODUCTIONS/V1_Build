from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ai_framework.models_extra import Integration
from core.db import get_session

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


class IntegrationIn(BaseModel):
    name: str
    type: str | None = None
    config: dict | None = None
    enabled: bool = False


class IntegrationOut(BaseModel):
    id: int
    name: str
    type: str | None
    config: dict | None
    enabled: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[IntegrationOut])
async def list_integrations():
    with get_session() as session:  # type: ignore
        rows = session.query(Integration).all()
        return [IntegrationOut.model_validate(r) for r in rows]


@router.post("/", response_model=IntegrationOut)
async def create_integration(body: IntegrationIn):
    with get_session() as session:  # type: ignore
        integ = Integration(name=body.name, type=body.type, config=body.config, enabled=body.enabled)
        session.add(integ)
        session.commit()
        session.refresh(integ)
        return IntegrationOut.model_validate(integ)




