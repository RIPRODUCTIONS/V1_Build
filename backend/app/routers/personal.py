from __future__ import annotations

from typing import Any, Dict, Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.tasks.personal_automation_tasks import (
    execute_personal_research,
    execute_personal_shopping,
    execute_personal_social,
    execute_personal_email,
    execute_personal_finance,
)
from app.agent.celery_app import celery_app
from celery.result import AsyncResult


router = APIRouter(prefix="/personal", tags=["personal"])


@router.post("/run/{template_id}")
def run_personal(template_id: str, payload: Dict[str, Any], db: Annotated[Session, Depends(get_db)]) -> Dict[str, Any]:
    if template_id == "research_assistant":
        job = execute_personal_research.delay(payload)
        return {"status": "queued", "task_id": job.id}
    if template_id == "shopping_assistant":
        job = execute_personal_shopping.delay(payload)
        return {"status": "queued", "task_id": job.id}
    if template_id == "social_media_manager":
        job = execute_personal_social.delay(payload)
        return {"status": "queued", "task_id": job.id}
    if template_id == "personal_email_manager":
        job = execute_personal_email.delay(payload)
        return {"status": "queued", "task_id": job.id}
    if template_id == "personal_finance_tracker":
        job = execute_personal_finance.delay(payload)
        return {"status": "queued", "task_id": job.id}
    return {"status": "unsupported", "template_id": template_id}


@router.get("/result/{task_id}")
def get_result(task_id: str) -> Dict[str, Any]:
    result: AsyncResult = celery_app.AsyncResult(task_id)
    state = result.state
    response: Dict[str, Any] = {"task_id": task_id, "state": state}
    if state == "SUCCESS":
        try:
            response["result"] = result.get(timeout=0)
            response["status"] = "completed"
        except Exception as exc:  # pragma: no cover - best effort
            response["status"] = "error"
            response["error"] = str(exc)
    elif state in {"FAILURE", "REVOKED"}:
        response["status"] = "error"
        try:
            response["error"] = str(result.result)
        except Exception:  # pragma: no cover
            pass
    else:
        response["status"] = "pending"
    return response

