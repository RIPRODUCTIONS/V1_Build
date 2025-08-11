from __future__ import annotations

from app.services.queue.redis_bus import RedisEventBus


class FakeRedis:
    def __init__(self) -> None:
        self.added: list[tuple[str, dict[str, str]]] = []

    def xadd(self, stream: str, fields: dict[str, str]) -> str:  # noqa: D401
        self.added.append((stream, fields))
        return "1-0"


def test_publish_ok(monkeypatch):
    bus = RedisEventBus(stream="events-test")

    bus._client = FakeRedis()  # type: ignore[attr-defined]
    msg_id = bus.publish({"a": 1})
    assert msg_id == "1-0"
