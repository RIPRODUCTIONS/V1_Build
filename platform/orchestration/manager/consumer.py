import json
import os
import signal
import time
from dataclasses import dataclass

# Import planner
try:
    from planner import planner
except ImportError:
    import sys

    sys.path.append(os.path.dirname(__file__))
    from planner import planner


@dataclass
class ConsumerConfig:
    input_stream: str = "events"
    output_stream: str = "manager_events"
    consumer_group: str = "manager_group"
    consumer_name: str = "manager_1"


class GracefulExit(Exception):
    pass

def extract_correlation_id(evt: dict | None) -> str | None:
    """Extract correlation_id from event dict with fallbacks.

    Order of preference: top-level -> headers.correlation_id -> meta.correlation_id.
    """
    if not isinstance(evt, dict):
        return None
    if isinstance(evt.get("correlation_id"), str) and evt.get("correlation_id"):
        return evt["correlation_id"]
    headers = evt.get("headers") or {}
    if isinstance(headers, dict) and isinstance(headers.get("correlation_id"), str):
        return headers.get("correlation_id")
    meta = evt.get("meta") or {}
    if isinstance(meta, dict) and isinstance(meta.get("correlation_id"), str):
        return meta.get("correlation_id")
    return None


def _install_signal_handlers():
    def _raise(sig, frame):
        raise GracefulExit

    for s in (signal.SIGINT, signal.SIGTERM):
        signal.signal(s, _raise)


def _publish(r, stream: str, event: dict):
    try:
        r.xadd(stream, {"data": json.dumps(event)})
        print(f"Published: {event.get('event_type')}")
    except Exception as e:
        print(f"Publish error: {e}")


def handle_event(evt: dict) -> list[dict]:
    """Handle automation.run.requested events."""
    if evt.get("event_type") != "automation.run.requested":
        return []

    intent = evt.get("intent")
    if not intent:
        return []

    # Create plan
    plan = planner.create_plan(
        run_id=evt.get("run_id") or "unknown",
        intent=intent,
        correlation_id=evt.get("correlation_id"),
    )

    # Return events to publish
    return [
        {
            "event_type": "run.started",
            "run_id": plan.run_id,
            "intent": plan.intent,
            "department": plan.department,
            "correlation_id": plan.correlation_id,
        },
        {
            "event_type": "run.status.updated",
            "run_id": plan.run_id,
            "status": "started",
            "intent": plan.intent,
            "department": plan.department,
            "correlation_id": plan.correlation_id,
        },
    ]


def consume_loop(cfg: ConsumerConfig):
    url = os.getenv("REDIS_URL")
    if not url:
        print("REDIS_URL not set")
        return

    try:
        import redis
    except ImportError:
        print("redis not installed")
        return

    r = redis.Redis.from_url(url, decode_responses=True)
    stream = cfg.input_stream
    group = cfg.consumer_group
    consumer = cfg.consumer_name

    # Setup consumer group
    try:
        r.xgroup_create(stream, group, id="0", mkstream=True)
        print(f"Created group {group} on {stream}")
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            print(f"Group setup error: {e}")

    _install_signal_handlers()
    print(f"Consumer started: {consumer} in {group} on {stream}")

    try:
        while True:
            try:
                # Read new messages only
                resp = r.xreadgroup(group, consumer, {stream: ">"}, block=1000, count=1)

                if not resp:
                    time.sleep(0.1)  # Small sleep to prevent spinning
                    continue

                for s, entries in resp:
                    for msg_id, fields in entries:
                        data = fields.get("data", "{}")
                        try:
                            evt = json.loads(data)
                        except:
                            evt = {"raw": data}

                        print(f"Processing: {evt.get('event_type', 'unknown')}")

                        # Handle event
                        events = handle_event(evt)
                        for event in events:
                            _publish(r, cfg.output_stream, event)

                        # Acknowledge
                        r.xack(stream, group, msg_id)
                        print(f"Acked: {msg_id}")

            except GracefulExit:
                raise
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

    except GracefulExit:
        print("Consumer stopped")


if __name__ == "__main__":
    consume_loop(ConsumerConfig())
