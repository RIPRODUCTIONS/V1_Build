from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import redis


@dataclass(slots=True)
class DLQItem:
    id: str
    queue_name: str
    payload: dict[str, Any]
    error_details: dict[str, Any]
    failed_at: str
    retry_count: int


class DeadLetterQueue:
    def __init__(self, redis_url: str | None = None) -> None:
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = redis.from_url(self.redis_url, decode_responses=True)

    def _key(self, queue_name: str) -> str:
        return f"dlq:{queue_name}"

    async def send_to_dlq(self, queue_name: str, failed_operation: dict[str, Any], error: Exception, context: dict[str, Any] | None = None) -> None:
        """Store failed operation with metadata; trim list by retention policy."""
        item = {
            "id": __import__("uuid").uuid4().hex,
            "queue_name": queue_name,
            "payload": failed_operation,
            "error_details": {"type": type(error).__name__, "str": str(error)},
            "failed_at": datetime.now(UTC).isoformat(),
            "retry_count": 0,
            "context": context or {},
        }
        await self._push(queue_name, item)

    async def _push(self, queue_name: str, item: dict[str, Any]) -> None:
        key = self._key(queue_name)
        self.client.lpush(key, json.dumps(item))
        # Trim to max size
        max_items = int(os.getenv("DLQ_MAX_ITEMS_PER_QUEUE", "1000"))
        self.client.ltrim(key, 0, max_items - 1)

    async def get_dlq_items(self, queue_name: str, limit: int = 50) -> list[DLQItem]:
        key = self._key(queue_name)
        raw = self.client.lrange(key, 0, limit - 1)
        out: list[DLQItem] = []
        for r in reversed(raw):  # oldest first
            d = json.loads(r)
            out.append(DLQItem(
                id=d.get("id"),
                queue_name=d.get("queue_name"),
                payload=d.get("payload"),
                error_details=d.get("error_details"),
                failed_at=d.get("failed_at"),
                retry_count=int(d.get("retry_count", 0)),
            ))
        return out

    async def replay_dlq_item(self, queue_name: str, item_id: str, replay_func) -> bool:
        """
        Replay a specific item by id using the provided replay_func(payload) -> bool.
        On success: remove from DLQ. On failure: increment retry_count and push back.
        """
        key = self._key(queue_name)
        # linear scan acceptable for small queues; can optimize with hash per id
        items = self.client.lrange(key, 0, -1)
        for raw in items:
            d = json.loads(raw)
            if d.get("id") != item_id:
                continue
            ok = False
            try:
                ok = bool(await replay_func(d.get("payload")))
            except Exception:  # requeue with increment
                d["retry_count"] = int(d.get("retry_count", 0)) + 1
                self._replace_item(key, raw, json.dumps(d))
                return False
            if ok:
                # remove
                self.client.lrem(key, 1, raw)
                return True
            else:
                d["retry_count"] = int(d.get("retry_count", 0)) + 1
                self._replace_item(key, raw, json.dumps(d))
                return False
        return False

    def _replace_item(self, key: str, old_raw: str, new_raw: str) -> None:
        pipe = self.client.pipeline()
        pipe.lrem(key, 1, old_raw)
        pipe.rpush(key, new_raw)
        pipe.execute()

    async def get_dlq_item(self, queue_name: str, item_id: str) -> dict[str, Any] | None:
        key = self._key(queue_name)
        for raw in self.client.lrange(key, 0, -1):
            d = json.loads(raw)
            if d.get("id") == item_id:
                return d
        return None

    async def bulk_replay_dlq_items(self, queue_name: str, item_ids: list[str], user_id: str, replay_func=None) -> dict[str, Any]:
        """Replay multiple DLQ items with simple concurrency control."""
        results: dict[str, Any] = {"success": 0, "failed": 0, "items": []}
        sem = __import__("asyncio").Semaphore(5)

        async def _replay_one(item_id: str) -> None:
            async with sem:
                func = replay_func or (lambda payload: True)
                ok = await self.replay_dlq_item(queue_name, item_id, func)
                results["items"].append({"id": item_id, "ok": bool(ok)})
                if ok:
                    results["success"] += 1
                else:
                    results["failed"] += 1

        await __import__("asyncio").gather(*[_replay_one(i) for i in item_ids])
        results["total"] = len(item_ids)
        results["queue"] = queue_name
        results["requested_by"] = user_id
        return results

    async def bulk_delete_dlq_items(self, queue_name: str, item_ids: list[str], user_id: str) -> dict[str, Any]:
        key = self._key(queue_name)
        items = self.client.lrange(key, 0, -1)
        deleted = 0
        for raw in list(items):
            d = json.loads(raw)
            if d.get("id") in set(item_ids):
                self.client.lrem(key, 1, raw)
                deleted += 1
        return {"deleted": deleted, "total": len(item_ids), "queue": queue_name, "requested_by": user_id}

    async def collect_dlq_metrics(self) -> dict[str, Any]:
        """Compute simple in-memory metrics for all queues (best-effort)."""
        metrics: dict[str, Any] = {}
        # Scan keys by prefix
        for key in self.client.scan_iter(match="dlq:*"):
            qname = key.split(":", 1)[1]
            count = self.client.llen(key)
            metrics[qname] = {"depth": count}
        return metrics

    async def generate_dlq_analytics_report(self) -> dict[str, Any]:
        m = await self.collect_dlq_metrics()
        return {"queues": m, "summary": {"total_items": sum(v["depth"] for v in m.values())}}


