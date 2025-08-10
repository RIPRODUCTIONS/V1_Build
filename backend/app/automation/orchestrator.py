from typing import Any

from app.automation.celery_app import celery
from app.automation.registry import get_dag, get_skill
from app.automation.state import set_status


async def run_dag(run_id: str, steps: list[str], context: dict[str, Any]) -> None:
    await set_status(run_id, "running", {"steps": steps})
    executed: list[str] = []
    try:
        for step in steps:
            fn = get_skill(step)
            context = await fn(context)
            executed.append(step)
        await set_status(run_id, "succeeded", {"executed": executed, "result": context})
    except Exception as e:  # pragma: no cover - simplest failure path
        await set_status(run_id, "failed", {"executed": executed, "error": str(e)})


@celery.task(name="automation.run_dag", bind=True, acks_late=True, max_retries=2)
def run_dag_task(self, run_id: str, intent: str, context: dict[str, Any]):
    import asyncio

    async def _run():
        steps: list[str] = get_dag(intent)
        await set_status(run_id, "running", {"steps": steps})
        executed: list[str] = []
        try:
            for step in steps:
                fn = get_skill(step)
                context_out = await fn(context)
                context.update(context_out)
                executed.append(step)
                await set_status(run_id, "running", {"executed": executed})
            await set_status(run_id, "succeeded", {"executed": executed, "result": context})
        except Exception as e:  # pragma: no cover - retry path
            if self.request.retries < self.max_retries:
                await set_status(run_id, "retrying", {"error": str(e), "executed": executed})
                raise self.retry(exc=e, countdown=2 * (self.request.retries + 1)) from None
            await set_status(run_id, "failed", {"error": str(e), "executed": executed})

    asyncio.run(_run())
