from __future__ import annotations

from typing import Any, Dict, Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.tasks.personal_automation_tasks import execute_personal_research, execute_personal_shopping


router = APIRouter(prefix="/personal", tags=["personal"])


@router.post("/run/{template_id}")
def run_personal(template_id: str, payload: Dict[str, Any], db: Annotated[Session, Depends(get_db)]) -> Dict[str, Any]:
    if template_id == "research_assistant":
        job = execute_personal_research.delay(payload)
        return {"status": "queued", "task_id": job.id}
    if template_id == "shopping_assistant":
        job = execute_personal_shopping.delay(payload)
        return {"status": "queued", "task_id": job.id}
    return {"status": "unsupported", "template_id": template_id}


