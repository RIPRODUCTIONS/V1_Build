from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis


class Scale700Manager:
    def __init__(self, redis_url: str) -> None:
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.active_workers: dict[str, list[dict[str, Any]]] = {}
        self.department_queues = {
            "finance": "queue:finance",
            "sales": "queue:sales",
            "marketing": "queue:marketing",
            "research": "queue:research",
            "operations": "queue:operations",
            "hr": "queue:hr",
            "legal": "queue:legal",
            "executive": "queue:executive",
        }

    async def start(self) -> None:
        for q in self.department_queues.values():
            try:
                await self.redis.lpush(q, json.dumps({"init": True}))
                await self.redis.lpop(q)
            except Exception:
                pass
        asyncio.create_task(self.auto_scaling_loop())

    async def auto_scaling_loop(self) -> None:
        while True:
            try:
                for dept, qname in self.department_queues.items():
                    depth = await self.redis.llen(qname)
                    workers = len(self.active_workers.get(dept, []))
                    if depth > max(1, workers) * 5:
                        await self.spawn_worker(dept)
                    elif depth < max(1, workers) * 2 and workers > 1:
                        await self.terminate_worker(dept)
                await asyncio.sleep(30)
            except Exception:
                await asyncio.sleep(60)

    async def spawn_worker(self, department: str) -> None:
        worker_id = f"{department}_{datetime.now(UTC).strftime('%H%M%S')}"
        self.active_workers.setdefault(department, []).append(
            {"id": worker_id, "started_at": datetime.now(UTC).isoformat(), "tasks_processed": 0, "status": "active"}
        )
        asyncio.create_task(self.worker_loop(department, worker_id))

    async def terminate_worker(self, department: str) -> None:
        arr = self.active_workers.get(department, [])
        if arr:
            arr.pop()

    async def worker_loop(self, department: str, worker_id: str) -> None:
        qname = self.department_queues[department]
        while True:
            try:
                res = await self.redis.brpop(qname, timeout=60)
                if res:
                    _key, data = res
                    _payload = json.loads(data)
                    # Simulate processing work; actual agent execution remains on backend server
                    await asyncio.sleep(0.05)
                    for w in self.active_workers.get(department, []):
                        if w.get("id") == worker_id:
                            w["tasks_processed"] = int(w.get("tasks_processed", 0)) + 1
                            break
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)




