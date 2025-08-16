from __future__ import annotations

from typing import Any

from app.web_operator.mvp_web_executor import MVPWebExecutor
from celery import shared_task


@shared_task(name="automation.execute_web_task")
def execute_web_automation_task(task_data: dict[str, Any]) -> dict[str, Any]:
    """Synchronous wrapper for the async MVP web executor.

    Uses shared_task so the primary Celery app (app.agent.celery_app) can discover it.
    """
    import asyncio

    async def _run() -> dict[str, Any]:
        executor = MVPWebExecutor()
        try:
            return await executor.execute_simple_web_task(
                task_description=str(task_data.get("description", "")),
                target_url=task_data.get("url"),
                correlation_id=task_data.get("correlation_id"),
            )
        except ModuleNotFoundError as e:
            # Playwright not present: return safe fallback
            return {"success": False, "reason": str(e), "url": task_data.get("url"), "description": task_data.get("description")}

    return asyncio.run(_run())


