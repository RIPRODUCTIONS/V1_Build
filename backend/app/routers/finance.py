from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.automation.idempotency import claim_or_get, store_result
from app.automation.orchestrator import run_dag_task
from app.automation.state import set_status

router = APIRouter(prefix='/finance', tags=['finance'])


class PayBillRequest(BaseModel):
    vendor: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    due_date: str | None = None
    invoice_number: str | None = None
    memo: str | None = None
    idempotency_key: str | None = None


class EnqueuedResponse(BaseModel):
    run_id: str
    status: str


@router.post('/pay_bill', response_model=EnqueuedResponse)
async def pay_bill(req: PayBillRequest) -> EnqueuedResponse:
    intent = 'finance.pay_bill'
    payload: dict[str, Any] = {
        'vendor': req.vendor,
        'amount': req.amount,
        'due_date': req.due_date,
        'invoice_number': req.invoice_number,
        'memo': req.memo,
    }
    key, cached = await claim_or_get(intent, payload, req.idempotency_key)
    if cached:
        return EnqueuedResponse(**cached)

    # Queue the automation DAG
    run_id = str(uuid.uuid4())
    await set_status(run_id, 'queued', {'intent': intent, 'payload': payload})
    try:
        run_dag_task.delay(run_id, intent, payload)
    except Exception as exc:  # pragma: no cover - queueing failure path
        raise HTTPException(status_code=503, detail=f'Queue unavailable: {exc}') from None

    resp = {'run_id': run_id, 'status': 'queued'}
    await store_result(key, resp)
    return EnqueuedResponse(**resp)
