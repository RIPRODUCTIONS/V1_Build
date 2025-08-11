from __future__ import annotations

import json
from pathlib import Path


def plan_next() -> dict:
    catalog = json.loads(
        (Path(__file__).resolve().parents[2] / "shared" / "catalog" / "tasks.json").read_text(
            encoding="utf-8"
        )
    )
    # naive pick: first task of each department
    steps = []
    for d in catalog.get("departments", []):
        tasks = d.get("tasks", [])
        if tasks:
            steps.append({"department": d["name"], "task": tasks[0]["key"]})
    return {"plan": steps}


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(plan_next(), indent=2))
