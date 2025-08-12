# ruff: noqa: I001
import hashlib
import json

import redis.asyncio as aioredis

from app.core.config import Settings


def _fingerprint(intent: str, payload: dict) -> str:
    raw = json.dumps({'intent': intent, 'payload': payload}, sort_keys=True).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


_IDEM_SEEN: set[str] = set()
_MEM_STORE: dict[str, str] = {}


async def claim_once(intent: str, payload: dict, idem_key: str | None, ttl_s: int = 600) -> str:
    s = Settings()
    key = idem_key or _fingerprint(intent, payload)
    namespaced = f'idem:{key}'
    try:
        r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
        ok = await r.set(namespaced, '1', ex=ttl_s, nx=True)
        if not ok:
            raise RuntimeError('Duplicate request (idempotency)')
    except Exception:
        # Fallback in-memory (best-effort for tests/CI without Redis)
        if namespaced in _IDEM_SEEN:
            raise RuntimeError('Duplicate request (idempotency)') from None
        _IDEM_SEEN.add(namespaced)
    return key


# Store-and-return idempotency (Stripe-style)
def _fp(intent: str, payload: dict) -> str:
    return hashlib.sha256(
        json.dumps({'i': intent, 'p': payload}, sort_keys=True).encode()
    ).hexdigest()


async def claim_or_get(intent: str, payload: dict, idem_key: str | None, ttl_s: int = 3600):
    key = f'idem:{idem_key or _fp(intent, payload)}'
    cached_obj = None
    try:
        s = Settings()
        r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
        ok = await r.set(key, '__PENDING__', ex=ttl_s, nx=True)
        if not ok:
            val = await r.get(key)
            if val and val != '__PENDING__':
                try:
                    cached_obj = json.loads(val)
                except Exception:  # pragma: no cover - tolerate bad cache
                    cached_obj = None
    except Exception:
        # Fallback in-memory for tests/CI without Redis
        cached = _MEM_STORE.get(key)
        if cached and cached != '__PENDING__':
            try:
                cached_obj = json.loads(cached)
            except Exception:
                cached_obj = None
        else:
            _MEM_STORE.setdefault(key, '__PENDING__')
    return key, cached_obj


async def store_result(key: str, response_obj: dict, ttl_s: int = 3600) -> None:
    try:
        s = Settings()
        r = aioredis.from_url(s.REDIS_URL, decode_responses=True)
        await r.set(key, json.dumps(response_obj), ex=ttl_s)
    except Exception:
        _MEM_STORE[key] = json.dumps(response_obj)
