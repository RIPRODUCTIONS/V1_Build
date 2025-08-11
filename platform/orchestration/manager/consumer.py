import json
import os
import signal
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


@dataclass
class ConsumerConfig:
    stream: str = "events"
    group: str | None = None
    consumer: str | None = None
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


def _maybe_start_metrics_server() -> None:
    port_raw = os.getenv("MANAGER_METRICS_PORT", "9109")
    try:
        port = int(port_raw)
    except Exception:
        port = 9109
    try:
        from prometheus_client import Counter, Gauge, Histogram, start_http_server

        start_http_server(port)
        global METRIC_EVENTS, METRIC_ERRORS, METRIC_LATENCY, METRIC_HEALTH  # noqa: PLW0603
        METRIC_EVENTS = Counter(
            "manager_events_consumed_total",
            "Total events consumed",
            ["stream"],
        )
        METRIC_ERRORS = Counter(
            "manager_consume_errors_total",
            "Total errors during consumption",
            []
        )
        METRIC_LATENCY = Histogram(
            "manager_consume_batch_latency_ms",
            "Latency per batch read in ms",
            []
        )
        METRIC_HEALTH = Gauge(
            "manager_health",
            "1 if healthy",
            []
        )
        METRIC_HEALTH.set(1)
        print(json.dumps({"level": "info", "msg": "metrics.start", "port": port}))
    except Exception as err:  # noqa: BLE001
        print(json.dumps({"level": "warn", "msg": "metrics.disabled", "error": str(err)}))


def _metric_inc(name: str, *labels: Any) -> None:
    # Avoid dynamic globals indexing per lint guidance
    m = METRIC_EVENTS if name == "METRIC_EVENTS" else (METRIC_ERRORS if name == "METRIC_ERRORS" else None)
    try:
        if m is not None:
            if labels:
                m.labels(*labels).inc()
            else:
                m.inc()
    except Exception:
        pass


def _metric_observe(name: str, value: float) -> None:
    # Avoid dynamic globals indexing per lint guidance
    m = METRIC_LATENCY if name == "METRIC_LATENCY" else None
    try:
        if m is not None:
            m.observe(value)
    except Exception:
        pass


def extract_correlation_id(evt: dict[str, Any]) -> str | None:
    candidates = [
        evt.get("correlation_id"),
        (evt.get("headers") or {}).get("correlation_id"),
        (evt.get("meta") or {}).get("correlation_id"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c
    return None


def _maybe_start_health_server() -> None:
    port_raw = os.getenv("MANAGER_HEALTH_PORT", "8011")
    try:
        port = int(port_raw)
    except Exception:
        port = 8011

    class Handler(BaseHTTPRequestHandler):  # pragma: no cover
        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args):  # noqa: A003
            return

    def run():  # pragma: no cover
        try:
            httpd = HTTPServer(("0.0.0.0", port), Handler)
            httpd.serve_forever()
        except Exception as err:  # noqa: BLE001
            print(json.dumps({"level": "warn", "msg": "health.disabled", "error": str(err)}))

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print(json.dumps({"level": "info", "msg": "health.start", "port": port}))


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
    _maybe_start_metrics_server()
    _maybe_start_health_server()
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
                        cid = extract_correlation_id(evt)
                        print(json.dumps({"level": "info", "msg": "consume", "stream": s, "id": _id, "correlation_id": cid, "event": evt}))
                        _metric_inc("METRIC_EVENTS", s)
                        if cfg.group:
                            r.xack(stream, cfg.group, _id)
                backoff = cfg.backoff_initial_ms
            except GracefulExit:
                raise
            except Exception as err:  # noqa: BLE001
                print(json.dumps({"level": "error", "msg": "consume.error", "error": str(err)}))
                _metric_inc("METRIC_ERRORS")
                time.sleep(backoff / 1000.0)
                backoff = min(cfg.backoff_max_ms, backoff * 2)
    except GracefulExit:
        print(json.dumps({"level": "info", "msg": "consumer.stop"}))


if __name__ == "__main__":  # pragma: no cover
    consume_loop(ConsumerConfig())
