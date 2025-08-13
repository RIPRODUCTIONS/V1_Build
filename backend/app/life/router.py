from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/life", tags=["life-orchestration"])


class OrchestrateResponse(BaseModel):
    run_id: str
    status: str


@router.post("/financial", response_model=OrchestrateResponse)
async def orchestrate_financial() -> OrchestrateResponse:
    return OrchestrateResponse(run_id="financial-boot", status="queued")


@router.post("/health", response_model=OrchestrateResponse)
async def orchestrate_health() -> OrchestrateResponse:
    return OrchestrateResponse(run_id="health-boot", status="queued")


@router.post("/professional", response_model=OrchestrateResponse)
async def orchestrate_professional() -> OrchestrateResponse:
    return OrchestrateResponse(run_id="professional-boot", status="queued")


@router.post("/personal", response_model=OrchestrateResponse)
async def orchestrate_personal() -> OrchestrateResponse:
    return OrchestrateResponse(run_id="personal-boot", status="queued")


