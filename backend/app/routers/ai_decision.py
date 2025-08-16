from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/operator/ai", tags=["operator:ai"])


@router.post("/analyze_task")
async def analyze_automation_task_endpoint(request: dict[str, Any]) -> dict[str, Any]:
    return {"status": "disabled", "request": request}


@router.post("/next_action")
async def determine_next_action_endpoint(request: dict[str, Any]) -> dict[str, Any]:
    return {"status": "disabled", "request": request}


