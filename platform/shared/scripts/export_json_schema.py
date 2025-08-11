from __future__ import annotations

import json
from pathlib import Path
from platform.shared.events import AutomationRunRequested

from app.routers.life import EnqueuedResponse, SimpleReq


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "schemas"
    out.mkdir(parents=True, exist_ok=True)
    schema = AutomationRunRequested.model_json_schema()
    (out / "automation_run_requested.schema.json").write_text(
        json.dumps(schema, indent=2), encoding="utf-8"
    )
    print(str(out / "automation_run_requested.schema.json"))
    # Export core API contracts used by life routes
    (out / "life_simple_req.schema.json").write_text(
        json.dumps(SimpleReq.model_json_schema(), indent=2), encoding="utf-8"
    )
    (out / "life_enqueued_response.schema.json").write_text(
        json.dumps(EnqueuedResponse.model_json_schema(), indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
