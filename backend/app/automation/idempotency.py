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


# Store-and-return idempotency (Stripe-style)
def _fp(intent: str, payload: dict) -> str:
    return hashlib.sha256(
        json.dumps({"i": intent, "p": payload}, sort_keys=True).encode()
    ).hexdigest()


async def claim_or_get(intent: str, payload: dict, idem_key: str | None, ttl_s: int = 3600):
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    key = f"idem:{idem_key or _fp(intent, payload)}"
    ok = await r.set(key, "__PENDING__", ex=ttl_s, nx=True)
    if ok:
        return key, None
    val = await r.get(key)
    if val and val != "__PENDING__":
        try:
            return key, json.loads(val)
        except Exception:  # pragma: no cover - tolerate bad cache
            return key, None
    return key, None


async def store_result(key: str, response_obj: dict, ttl_s: int = 3600) -> None:
    s = Settings()
    r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
    await r.set(key, json.dumps(response_obj), ex=ttl_s)
