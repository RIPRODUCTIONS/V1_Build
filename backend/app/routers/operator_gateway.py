from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.core.config import get_settings


router = APIRouter(prefix="/operator", tags=["operator:gateway"])


@router.post("/execute")
async def execute_automation_task(request: Dict[str, Any], settings=Depends(get_settings)) -> Dict[str, Any]:
    # Queue minimal web task into Celery if operator is enabled
    if settings.OPERATOR_WEB_ENABLED:
        try:
            from app.tasks.web_automation_tasks import execute_web_automation_task

            task = execute_web_automation_task.delay({
                "description": request.get("description", ""),
                "url": request.get("url"),
            })
            return {"status": "queued", "task_id": task.id}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}
    return {"status": "disabled", "message": "Web operator disabled"}


@router.get("/status")
async def get_operator_status(settings=Depends(get_settings)) -> Dict[str, Any]:
    return {
        "web_enabled": settings.OPERATOR_WEB_ENABLED,
        "desktop_enabled": settings.OPERATOR_DESKTOP_ENABLED,
        "queues": {"high": 0, "normal": 0, "low": 0},
    }


# Placeholder for future websocket route (FastAPI websockets). HTTP stub for now
@router.get("/tasks/{task_id}/stream")
async def stream_task_progress(task_id: str) -> Dict[str, Any]:
    return {"task_id": task_id, "stream": "disabled"}


