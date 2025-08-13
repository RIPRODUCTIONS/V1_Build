from __future__ import annotations

from typing import Any, Dict

from celery import shared_task
from app.operator.mvp_web_executor import MVPWebExecutor


@shared_task(name="automation.execute_web_task")
def execute_web_automation_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for the async MVP web executor.

    Uses shared_task so the primary Celery app (app.agent.celery_app) can discover it.
    """
    import asyncio

    async def _run() -> Dict[str, Any]:
        executor = MVPWebExecutor()
        return await executor.execute_simple_web_task(
            task_description=str(task_data.get("description", "")),
            target_url=task_data.get("url"),
            correlation_id=task_data.get("correlation_id"),
        )

    return asyncio.run(_run())


