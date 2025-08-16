from __future__ import annotations

import pytest

from app.automation import idempotency as idem


@pytest.mark.asyncio
async def test_claim_once_duplicate_memory(monkeypatch):
    # Force in-memory fallback by making Redis URL invalid
    monkeypatch.setenv("REDIS_URL", "redis://invalid:0/0")
    key = await idem.claim_once("intent.alpha", {"a": 1}, idem_key=None, ttl_s=10)
    assert isinstance(key, str) and key
    # Same key should be rejected as duplicate
    with pytest.raises(RuntimeError):
        await idem.claim_once("intent.alpha", {"a": 1}, idem_key=key, ttl_s=10)


@pytest.mark.asyncio
async def test_claim_or_get_and_store_result(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://invalid:0/0")
    key1, cached1 = await idem.claim_or_get("intent.beta", {"x": 1}, idem_key=None, ttl_s=5)
    assert isinstance(key1, str) and cached1 is None
    await idem.store_result(key1, {"ok": True})
    # Call again with same intent/payload (same derived key) → should return cached object
    key2, cached2 = await idem.claim_or_get("intent.beta", {"x": 1}, idem_key=None, ttl_s=5)
    assert key2 == key1
    assert cached2 == {"ok": True}


