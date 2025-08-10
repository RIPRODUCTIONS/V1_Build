# ruff: noqa: I001
import asyncio
import uuid

from fastapi import APIRouter, HTTPException

from app.automation.idempotency import claim_once
from app.automation.orchestrator import run_dag
from app.automation.registry import register_dag
from app.automation.schemas import AutomationEnqueued, AutomationStatus, AutomationSubmit
from app.automation.state import get_status

router = APIRouter(prefix="/automation", tags=["automation"])

# Example DAGs
register_dag("lead.intake", ["lead.create_record", "lead.schedule_followup"])
register_dag("finance.pay_bill", ["finance.ocr_and_categorize", "finance.schedule_payment"])
register_dag("agent.prototype", ["prototype.enqueue_build"])


@router.post("/submit", response_model=AutomationEnqueued)
async def submit(req: AutomationSubmit):
    try:
        _ = await claim_once(req.intent, req.payload, req.idempotency_key)
    except RuntimeError:
        raise HTTPException(status_code=409, detail="Duplicate idempotent request") from None
    run_id = str(uuid.uuid4())
    steps = register_dag.__globals__["_DAGS"][req.intent]
    asyncio.create_task(run_dag(run_id, steps=steps, context=req.payload))
    return AutomationEnqueued(run_id=run_id)


@router.get("/runs/{run_id}", response_model=AutomationStatus)
async def status(run_id: str):
    st = await get_status(run_id)
    return AutomationStatus(run_id=run_id, status=st["status"], detail=st.get("detail"))
