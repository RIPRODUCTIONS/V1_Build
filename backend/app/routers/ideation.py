from __future__ import annotations

import uuid
from typing import Any

from app.automation.idempotency import claim_or_get, store_result
from app.automation.orchestrator import run_dag_task
from app.automation.state import set_status
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ideation", tags=["ideation"])


class IdeationRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    count: int | None = 5
    idempotency_key: str | None = None


class EnqueuedResponse(BaseModel):
    run_id: str
    status: str


@router.post("/generate", response_model=EnqueuedResponse)
async def generate(req: IdeationRequest) -> EnqueuedResponse:
    intent = "ideation.generate"
    payload: dict[str, Any] = {"topic": req.topic, "count": req.count or 5}
    key, cached = await claim_or_get(intent, payload, req.idempotency_key)
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
