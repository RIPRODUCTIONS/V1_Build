from typing import Any

from app.automation.registry import get_skill
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
