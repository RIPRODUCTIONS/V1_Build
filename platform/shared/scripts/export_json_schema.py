from __future__ import annotations

import json
from pathlib import Path

from platform.shared.events import AutomationRunRequested


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "schemas"
    out.mkdir(parents=True, exist_ok=True)
    schema = AutomationRunRequested.model_json_schema()
    (out / "automation_run_requested.schema.json").write_text(
        json.dumps(schema, indent=2), encoding="utf-8"
    )
    print(str(out / "automation_run_requested.schema.json"))


if __name__ == "__main__":
    main()



