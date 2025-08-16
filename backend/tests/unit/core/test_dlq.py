import json
import pytest


class _FakeRedis:
    def __init__(self):
        self.store: dict[str, list[str]] = {}

    def from_url(self, *_a, **_k):  # type: ignore
        return self

    # List ops
    def lpush(self, key, value):
        self.store.setdefault(key, []).insert(0, value)

    def ltrim(self, key, start, end):
        lst = self.store.get(key, [])
        self.store[key] = lst[start : end + 1]

    def lrange(self, key, start, end):
        lst = self.store.get(key, [])
        if end == -1:
            return lst[start:]
        return lst[start : end + 1]

    def lrem(self, key, count, value):
        lst = self.store.get(key, [])
        removed = 0
        out = []
        for v in lst:
            if removed < count and v == value:
                removed += 1
            else:
                out.append(v)
        self.store[key] = out
        return removed

    def rpush(self, key, value):
        self.store.setdefault(key, []).append(value)

    def pipeline(self):
        class P:
            def __init__(self, outer):
                self.outer = outer
                self.ops = []
            def lrem(self, *a, **k): self.ops.append(("lrem", a, k))
            def rpush(self, *a, **k): self.ops.append(("rpush", a, k))
            def execute(self):
                for op, a, k in self.ops:
                    getattr(self.outer, op)(*a, **k)
        return P(self)

    def scan_iter(self, match):
        for k in list(self.store.keys()):
            if k.startswith(match[:-1]):
                yield k

    def llen(self, key):
        return len(self.store.get(key, []))


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    import types
    from app.core import dlq as dlq_module
    fake = _FakeRedis()
    mod = types.SimpleNamespace(from_url=lambda *_a, **_k: fake)
    monkeypatch.setattr(dlq_module, 'redis', mod, raising=True)
    yield


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dlq_send_and_get_items():
    from app.core.dlq import DeadLetterQueue
    dlq = DeadLetterQueue(redis_url="redis://ignored")
    await dlq.send_to_dlq("system", {"x": 1}, RuntimeError("boom"))
    items = await dlq.get_dlq_items("system", limit=10)
    assert len(items) == 1
    it = items[0]
    assert it.queue_name == "system"
    assert it.retry_count == 0
    assert it.payload == {"x": 1}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dlq_replay_and_delete():
    from app.core.dlq import DeadLetterQueue
    dlq = DeadLetterQueue(redis_url="redis://ignored")
    await dlq.send_to_dlq("sys", {"a": 1}, RuntimeError("e"))
    items = await dlq.get_dlq_items("sys", limit=10)
    item_id = items[0].id

    async def ok_replay(payload):
        return True

    ok = await dlq.replay_dlq_item("sys", item_id, ok_replay)
    assert ok is True
    # queue should now be empty
    assert await dlq.get_dlq_items("sys", 10) == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_dlq_metrics_and_report():
    from app.core.dlq import DeadLetterQueue
    dlq = DeadLetterQueue(redis_url="redis://ignored")
    for i in range(3):
        await dlq.send_to_dlq("q1", {"i": i}, RuntimeError("x"))
    m = await dlq.collect_dlq_metrics()
    assert m["q1"]["depth"] == 3
    rep = await dlq.generate_dlq_analytics_report()
    assert rep["summary"]["total_items"] == 3


