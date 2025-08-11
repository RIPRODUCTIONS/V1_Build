from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/departments", tags=["departments"])


def _catalog() -> dict[str, Any]:
    p = Path(__file__).resolve().parents[3] / "platform" / "shared" / "catalog" / "tasks.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    return data


@router.get("/")
def list_departments() -> dict[str, Any]:
    data = _catalog()
    departments = []

    for dept in data.get("departments", []):
        departments.append(
            {
                "id": dept["name"],
                "name": dept["name"].title(),
                "description": f"AI department specializing in {dept['name']} automation and optimization",
                "capabilities": [
                    "Automated task execution",
                    "Intelligent decision making",
                    "Continuous learning",
                    "Performance optimization",
                ],
                "task_count": len(dept.get("tasks", [])),
            }
        )

    return {"items": departments}


@router.get("/tasks/catalog")
def tasks_catalog() -> dict[str, Any]:
    data = _catalog()
    tasks = []

    for dept in data.get("departments", []):
        for task in dept.get("tasks", []):
            # Parse task key to get complexity and duration
            task_parts = task["key"].split(".")
            complexity = "medium"  # Default complexity
            duration = "5-15 minutes"  # Default duration

            if "daily" in task["key"]:
                complexity = "low"
                duration = "2-5 minutes"
            elif "weekly" in task["key"]:
                complexity = "medium"
                duration = "10-20 minutes"
            elif "monthly" in task["key"]:
                complexity = "high"
                duration = "30-60 minutes"

            tasks.append(
                {
                    "id": task["key"],
                    "name": task["key"].replace("_", " ").replace(".", " - ").title(),
                    "description": f"Automated {task['key']} task for {dept['name']} department",
                    "department": dept["name"],
                    "complexity": complexity,
                    "estimated_duration": duration,
                    "dependencies": [],
                }
            )

    return {"tasks": tasks}
