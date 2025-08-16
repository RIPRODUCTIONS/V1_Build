from typing import Any

from app.core.config import get_settings
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/operator/desktop", tags=["operator:desktop"])


@router.post("/tasks")
async def create_desktop_automation_task(task: dict[str, Any], settings=Depends(get_settings)) -> dict[str, Any]:  # noqa: B008
    if not settings.OPERATOR_DESKTOP_ENABLED:
        return {"status": "disabled", "message": "Desktop operator disabled"}
    return {"status": "queued", "task": task}


@router.get("/tasks/{task_id}/screenshot")
async def get_task_screenshot(task_id: str, settings=Depends(get_settings)) -> dict[str, Any]:  # noqa: B008
    if not settings.OPERATOR_DESKTOP_ENABLED:
        return {"status": "disabled", "task_id": task_id}
    return {"status": "unavailable", "task_id": task_id}


