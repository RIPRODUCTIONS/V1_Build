from __future__ import annotations

import json
from pathlib import Path

from shared.events import (
    AutomationRunRequested,
    RunCompleted,
    RunFailed,
    RunLogEntry,
    RunStarted,
    RunStatusUpdated,
)

try:
    from app.routers.life import EnqueuedResponse, SimpleReq  # when running from repo root
except Exception:  # pragma: no cover - optional import for schema convenience
    EnqueuedResponse = None  # type: ignore
    SimpleReq = None  # type: ignore


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "schemas"
    out.mkdir(parents=True, exist_ok=True)

    # Export all event schemas
    events = {
        "automation_run_requested": AutomationRunRequested,
        "run_status_updated": RunStatusUpdated,
        "run_started": RunStarted,
        "run_completed": RunCompleted,
        "run_failed": RunFailed,
        "run_log_entry": RunLogEntry,
    }

    for name, event_class in events.items():
        schema_file = out / f"{name}.schema.json"
        schema_file.write_text(
            json.dumps(event_class.model_json_schema(), indent=2), encoding="utf-8"
        )
        print(f"Exported {name}.schema.json")

    # Export core API contracts used by life routes (if available in PYTHONPATH)
    if SimpleReq is not None and EnqueuedResponse is not None:
        (out / "life_simple_req.schema.json").write_text(
            json.dumps(SimpleReq.model_json_schema(), indent=2), encoding="utf-8"
        )
        (out / "life_enqueued_response.schema.json").write_text(
            json.dumps(EnqueuedResponse.model_json_schema(), indent=2), encoding="utf-8"
        )
        print("Exported life API schemas")


if __name__ == "__main__":
    main()
