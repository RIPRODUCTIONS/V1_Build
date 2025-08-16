import asyncio
import json
import types
from typing import Any, Dict, List, Tuple

import pytest


class _FakeRedisAsync:
    def __init__(self, entries: List[Tuple[str, Dict[str, Any]]] | None = None, group_exists: bool = True):
        self._entries = entries or []
        self._group_exists = group_exists
        self._acks: List[str] = []
        self._dlq: List[str] = []
        self._processed: set[str] = set()
        self._xread_calls = 0

    # Context/connection lifecycle
    async def aclose(self):
        return None

    # Stream ops
    async def xadd(self, stream: str, fields: Dict[str, str]):
        # Return a Redis-like id string
        return "1-0"

    async def xgroup_create(self, stream: str, group: str, id: str, mkstream: bool):
        if self._group_exists:
            raise Exception("BUSYGROUP Consumer Group name already exists")
        return "OK"

    async def xreadgroup(self, group: str, name: str, streams: Dict[str, str], count: int, block: int):
        self._xread_calls += 1
        if not self._entries:
            # End the loop after first poll for tests
            raise asyncio.CancelledError()
        # Return once, then cancel on next call
        if self._xread_calls > 1:
            raise asyncio.CancelledError()
        # Pack entries to Redis response structure: [(stream, [(id, {fields})])]
        return [(next(iter(streams.keys())), [(eid, {"e": json.dumps(payload)}) for eid, payload in self._entries])]

    # Sets for idempotency
    async def sismember(self, key: str, member: str) -> int:
        return 1 if member in self._processed else 0

    async def sadd(self, key: str, member: str):
        self._processed.add(member)
        return 1

    async def scard(self, key: str) -> int:
        return len(self._processed)

    async def spop(self, key: str):
        if self._processed:
            self._processed.pop()
        return None

    # Acks
    async def xack(self, stream: str, group: str, entry_id: str):
        self._acks.append(entry_id)
        return 1

    # DLQ
    async def lpush(self, key: str, value: str):
        self._dlq.append(value)
        return len(self._dlq)


@pytest.mark.asyncio
async def test_event_publish_success(monkeypatch):
    from app.core import event_bus as mod

    fake = _FakeRedisAsync()
    monkeypatch.setattr(mod, "redis", types.SimpleNamespace(from_url=lambda _url: fake))

    bus = mod.SystemEventBus()
    eid = await bus.publish("automation_started", {"id": 123}, source="test")
    assert isinstance(eid, str)


@pytest.mark.asyncio
async def test_subscribe_and_consume_handler(monkeypatch):
    from app.core import event_bus as mod

    payload = {"type": "automation_completed", "data": {"ok": True}}
    fake = _FakeRedisAsync(entries=[("1-1", payload)])
    monkeypatch.setattr(mod, "redis", types.SimpleNamespace(from_url=lambda _url: fake))

    bus = mod.SystemEventBus()
    seen: list[dict[str, Any]] = []

    async def handler(evt: dict[str, Any]):
        seen.append(evt)

    await bus.subscribe("automation_completed", handler)
    with pytest.raises(asyncio.CancelledError):
        await bus.consume(group="g1", name="n1", count=10, block_ms=10)

    assert seen and seen[0]["type"] == "automation_completed"
    # Acknowledged and marked processed
    assert "1-1" in fake._acks
    assert "1-1" in fake._processed


@pytest.mark.asyncio
async def test_idempotent_skip(monkeypatch):
    from app.core import event_bus as mod

    payload = {"type": "automation_started", "data": {"x": 1}}
    fake = _FakeRedisAsync(entries=[("1-2", payload)])
    # Pre-mark as processed
    fake._processed.add("1-2")
    monkeypatch.setattr(mod, "redis", types.SimpleNamespace(from_url=lambda _url: fake))

    bus = mod.SystemEventBus()
    seen: list[dict[str, Any]] = []

    async def handler(evt: dict[str, Any]):
        seen.append(evt)

    await bus.subscribe("automation_started", handler)
    with pytest.raises(asyncio.CancelledError):
        await bus.consume(group="g1", name="n1", count=10, block_ms=10)

    # Handler should not be called; entry should be acked
    assert not seen
    assert "1-2" in fake._acks


@pytest.mark.asyncio
async def test_handler_exception_goes_to_dlq(monkeypatch):
    from app.core import event_bus as mod

    payload = {"type": "automation_failed", "data": {"reason": "x"}}
    fake = _FakeRedisAsync(entries=[("1-3", payload)])
    monkeypatch.setattr(mod, "redis", types.SimpleNamespace(from_url=lambda _url: fake))

    bus = mod.SystemEventBus()

    async def handler(_evt: dict[str, Any]):
        raise RuntimeError("boom")

    await bus.subscribe("automation_failed", handler)
    with pytest.raises(asyncio.CancelledError):
        await bus.consume(group="g1", name="n1", count=10, block_ms=10)

    assert fake._dlq, "Expected DLQ push when handler errors"
    dlq_item = json.loads(fake._dlq[0])
    assert dlq_item.get("id") == "1-3"



