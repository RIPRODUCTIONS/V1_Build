# ruff: noqa: I001
import uuid

from fastapi import APIRouter, HTTPException

from app.automation.idempotency import claim_or_get, store_result
from app.automation.orchestrator import run_dag_task
from app.automation.registry import get_dag
from app.automation.schemas import AutomationEnqueued, AutomationStatus, AutomationSubmit
from app.automation.state import get_status, list_recent, record_run_meta, set_status

router = APIRouter(prefix="/automation", tags=["automation"])


@router.post("/submit", response_model=AutomationEnqueued)
async def submit(req: AutomationSubmit):
    if req.intent not in get_dag.__globals__["_DAGS"]:
        raise HTTPException(status_code=400, detail="Unknown intent")
    key, cached = await claim_or_get(req.intent, req.payload, req.idempotency_key)
    if cached:
        return AutomationEnqueued(**cached)
    run_id = str(uuid.uuid4())
    await set_status(run_id, "queued", {"intent": req.intent})
    await record_run_meta(run_id, req.intent, req.payload)
    run_dag_task.delay(run_id, req.intent, req.payload)
    resp = {"run_id": run_id, "status": "queued"}
    await store_result(key, resp)
    return AutomationEnqueued(**resp)


@router.get("/runs/{run_id}", response_model=AutomationStatus)
async def status(run_id: str):
    st = await get_status(run_id)
    return AutomationStatus(run_id=run_id, status=st["status"], detail=st.get("detail"))


@router.get("/recent")
async def recent(limit: int = 20):
    items = await list_recent(limit=limit)
    return {"items": items}
