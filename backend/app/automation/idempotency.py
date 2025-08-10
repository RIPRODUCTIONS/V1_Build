# ruff: noqa: I001
import hashlib
import json

import redis.asyncio as aioredis

from app.core.config import Settings


def _fingerprint(intent: str, payload: dict) -> str:
    raw = json.dumps({"intent": intent, "payload": payload}, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


_IDEM_SEEN: set[str] = set()


async def claim_once(intent: str, payload: dict, idem_key: str | None, ttl_s: int = 600) -> str:
    s = Settings()
    key = idem_key or _fingerprint(intent, payload)
    namespaced = f"idem:{key}"
    try:
        r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
        ok = await r.set(namespaced, "1", ex=ttl_s, nx=True)
        if not ok:
            raise RuntimeError("Duplicate request (idempotency)")
    except Exception:
        # Fallback in-memory (best-effort for tests/CI without Redis)
        if namespaced in _IDEM_SEEN:
            raise RuntimeError("Duplicate request (idempotency)") from None
        _IDEM_SEEN.add(namespaced)
    return key
