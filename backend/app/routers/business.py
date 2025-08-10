from __future__ import annotations

import uuid
from typing import Any

from app.automation.idempotency import claim_or_get, store_result
from app.automation.orchestrator import run_dag_task
from app.automation.state import set_status
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/business", tags=["business"])


class MarketingLaunchRequest(BaseModel):
    campaign_name: str = Field(..., min_length=1)
    channels: list[str] | None = None
    idempotency_key: str | None = None


class SalesOutreachRequest(BaseModel):
    leads: list[str] = Field(default_factory=list)
    template: str | None = None
    idempotency_key: str | None = None


class EnqueuedResponse(BaseModel):
    run_id: str
    status: str


async def _enqueue(intent: str, payload: dict[str, Any], idem: str | None) -> EnqueuedResponse:
    key, cached = await claim_or_get(intent, payload, idem)
    if cached:
        return EnqueuedResponse(**cached)
    run_id = str(uuid.uuid4())
    await set_status(run_id, "queued", {"intent": intent, "payload": payload})
    try:
        run_dag_task.delay(run_id, intent, payload)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Queue unavailable: {exc}") from None
    resp = {"run_id": run_id, "status": "queued"}
    await store_result(key, resp)
    return EnqueuedResponse(**resp)


@router.post("/marketing/launch", response_model=EnqueuedResponse)
async def marketing_launch(req: MarketingLaunchRequest) -> EnqueuedResponse:
    payload: dict[str, Any] = {
        "campaign_name": req.campaign_name,
        "channels": req.channels or ["email"],
    }
    return await _enqueue("business.marketing_launch", payload, req.idempotency_key)


@router.post("/sales/outreach", response_model=EnqueuedResponse)
async def sales_outreach(req: SalesOutreachRequest) -> EnqueuedResponse:
    payload: dict[str, Any] = {"leads": req.leads, "template": req.template or "hi {{name}}"}
    return await _enqueue("business.sales_outreach", payload, req.idempotency_key)


@router.post("/ops/brief", response_model=EnqueuedResponse)
async def ops_brief() -> EnqueuedResponse:
    return await _enqueue("business.ops_brief", {}, None)
