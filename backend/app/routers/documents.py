from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.automation.idempotency import claim_or_get, store_result
from app.automation.orchestrator import run_dag
from app.automation.state import set_status

router = APIRouter(prefix='/documents', tags=['documents'])


class IngestRequest(BaseModel):
    files: list[str]
    idempotency_key: str | None = None


class EnqueuedResponse(BaseModel):
    run_id: str
    status: str


@router.post('/ingest_scan', response_model=EnqueuedResponse)
async def ingest_scan(req: IngestRequest) -> EnqueuedResponse:
    intent = 'documents.ingest_scan'
    payload: dict[str, Any] = {'files': req.files}
    key, cached = await claim_or_get(intent, payload, req.idempotency_key)
    if cached:
        return EnqueuedResponse(**cached)
    run_id = str(uuid.uuid4())
    await set_status(run_id, 'queued', {'intent': intent})
    # Inline execution to ensure completion without external broker
    steps = [
        'documents.ocr_scan',
        'documents.classify',
        'documents.layout_analyze',
        'documents.extract_text',
    ]
    await run_dag(run_id, steps, dict(payload))
    resp = {'run_id': run_id, 'status': 'queued'}
    await store_result(key, resp)
    return EnqueuedResponse(**resp)
