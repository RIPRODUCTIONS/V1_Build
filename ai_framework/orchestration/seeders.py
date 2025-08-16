from __future__ import annotations

import time

from core.queue import TaskQueue


async def continuous_seeds() -> None:
    q = TaskQueue()
    await q.connect()
    now = int(time.time())
    seeds = [
        {
            "agent_id": "ai_market_researcher",
            "task": {
                "task_id": f"mr_{now}",
                "task_type": "market_research",
                "description": "Scan competitors",
                "requirements": {},
                "metadata": {},
            },
        },
        {
            "agent_id": "ai_content_creator",
            "task": {
                "task_id": f"mk_{now}",
                "task_type": "content_creation",
                "description": "Write blog outline",
                "requirements": {},
                "metadata": {},
            },
        },
        {
            "agent_id": "ai_sales_manager",
            "task": {
                "task_id": f"sl_{now}",
                "task_type": "lead_intake",
                "description": "Qualify leads",
                "requirements": {},
                "metadata": {},
            },
        },
    ]
    for s in seeds:
        await q.enqueue({"agent_id": s["agent_id"], "task": s["task"], "attempts": 0})




