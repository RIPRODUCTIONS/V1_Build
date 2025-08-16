from __future__ import annotations

import hashlib
import hmac
import time

import redis.asyncio as redis


class WebhookSecurity:
    def __init__(self, secret_key: str, redis_client: redis.Redis, nonce_ttl: int = 300):
        self.secret_key = secret_key
        self.redis = redis_client
        self.nonce_ttl = nonce_ttl

    async def validate(self, *, raw_body: bytes, headers: dict[str, str]) -> tuple[bool, str | None]:
        sig = headers.get("X-Atomic-Signature") or headers.get("X-Signature")
        ts = headers.get("X-Atomic-Timestamp") or headers.get("X-Timestamp")
        nonce = headers.get("X-Atomic-Nonce") or headers.get("X-Nonce")
        if not sig or not ts or not nonce:
            return False, "missing_signature_headers"
        try:
            ts_i = int(ts)
        except Exception:
            return False, "invalid_timestamp"
        now = int(time.time())
        if abs(now - ts_i) > self.nonce_ttl:
            return False, "stale_timestamp"
        # Nonce replay
        nonce_key = f"atomic:webhook:nonce:{nonce}"
        if await self.redis.exists(nonce_key):
            return False, "replay"
        await self.redis.setex(nonce_key, self.nonce_ttl, "1")
        # HMAC
        expected = hmac.new(self.secret_key.encode(), raw_body + ts.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig.removeprefix("sha256="), expected):
            return False, "bad_signature"
        return True, None







