from __future__ import annotations

import uuid
from typing import Any

from app.automation.idempotency import claim_or_get, store_result
from app.automation.orchestrator import run_dag
from app.automation.state import set_status
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/life", tags=["life-automation"])


class SimpleReq(BaseModel):
    payload: dict[str, Any] | None = None
    idempotency_key: str | None = None


class EnqueuedResponse(BaseModel):
    run_id: str
    status: str


async def _inline(
    intent: str, payload: dict[str, Any] | None, idem_key: str | None
) -> EnqueuedResponse:
    p = payload or {}
    key, cached = await claim_or_get(intent, p, idem_key)
    if cached:
        return EnqueuedResponse(**cached)
    run_id = str(uuid.uuid4())
    await set_status(run_id, "queued", {"intent": intent})
    # Directly enqueue orchestration; steps are resolved by orchestrator from registered DAGs
    await run_dag(run_id, [], dict(p))
    resp = {"run_id": run_id, "status": "queued"}
    await store_result(key, resp)
    return EnqueuedResponse(**resp)


@router.post("/health/wellness", response_model=EnqueuedResponse)
async def wellness(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("health.wellness_daily", {}, None)


@router.post("/nutrition/plan", response_model=EnqueuedResponse)
async def nutrition(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("nutrition.plan", {}, None)


@router.post("/home/evening", response_model=EnqueuedResponse)
async def home(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("home.evening_scene", {}, None)


@router.post("/transport/commute", response_model=EnqueuedResponse)
async def transport(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("transport.commute", {}, None)


@router.post("/learning/upskill", response_model=EnqueuedResponse)
async def learning(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("learning.upskill", {}, None)


@router.post("/finance/investments", response_model=EnqueuedResponse)
async def finance_investments(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("finance.investments_daily", {}, None)


@router.post("/finance/bills", response_model=EnqueuedResponse)
async def finance_bills(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("finance.bills_monthly", {}, None)


@router.post("/security/sweep", response_model=EnqueuedResponse)
async def security_sweep(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("security.weekly_sweep", {}, None)


@router.post("/travel/plan", response_model=EnqueuedResponse)
async def travel_plan(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("travel.plan", {}, None)


@router.post("/calendar/organize", response_model=EnqueuedResponse)
async def calendar_organize(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("calendar.organize_day", {}, None)


@router.post("/shopping/optimize", response_model=EnqueuedResponse)
async def shopping_optimize(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("shopping.optimize", {}, None)
