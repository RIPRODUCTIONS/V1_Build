from __future__ import annotations

import json
import os
import signal
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConsumerConfig:
    stream: str = "events"
    group: Optional[str] = None
    consumer: Optional[str] = None
    block_ms: int = 1000
    backoff_initial_ms: int = 250
    backoff_max_ms: int = 5000


class GracefulExit(Exception):
    pass


def _install_signal_handlers():  # pragma: no cover
    def _raise(sig, frame):  # noqa: ARG001
        raise GracefulExit

    for s in (signal.SIGINT, signal.SIGTERM):
        signal.signal(s, _raise)


def consume_loop(cfg: ConsumerConfig) -> None:  # pragma: no cover - dev utility
    url = os.getenv("REDIS_URL")
    if not url:
        print(json.dumps({"level": "warn", "msg": "REDIS_URL not set; consumer idle"}))
        return
    try:
        import redis  # type: ignore
    except Exception:
        print(json.dumps({"level": "warn", "msg": "redis client not installed"}))
        return
    r = redis.Redis.from_url(url, decode_responses=True)
    stream = cfg.stream
    last_id = ">$" if not cfg.group else "0-0"
    backoff = cfg.backoff_initial_ms
    _install_signal_handlers()
    print(json.dumps({"level": "info", "msg": "consumer.start", "stream": stream}))
    try:
        while True:
            try:
                if cfg.group:
                    resp = r.xreadgroup(cfg.group, cfg.consumer or "c1", {stream: last_id}, block=cfg.block_ms, count=1)
                else:
                    resp = r.xread({stream: last_id}, block=cfg.block_ms, count=1)
                if not resp:
                    backoff = cfg.backoff_initial_ms
                    continue
                for s, entries in resp:
                    for _id, fields in entries:
                        data = fields.get("data")
                        try:
                            evt = json.loads(data or "{}")
                        except Exception:
                            evt = {"raw": data}
                        print(json.dumps({"level": "info", "msg": "consume", "stream": s, "id": _id, "event": evt}))
                        if cfg.group:
                            r.xack(stream, cfg.group, _id)
                backoff = cfg.backoff_initial_ms
            except GracefulExit:
                raise
            except Exception as err:  # noqa: BLE001
                print(json.dumps({"level": "error", "msg": "consume.error", "error": str(err)}))
                time.sleep(backoff / 1000.0)
                backoff = min(cfg.backoff_max_ms, backoff * 2)
    except GracefulExit:
        print(json.dumps({"level": "info", "msg": "consumer.stop"}))


if __name__ == "__main__":  # pragma: no cover
    consume_loop(ConsumerConfig())
