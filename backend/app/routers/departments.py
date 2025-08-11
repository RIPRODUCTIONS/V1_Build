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
    return {"items": [d["name"] for d in data.get("departments", [])]}


@router.get("/tasks/catalog")
def tasks_catalog() -> dict[str, Any]:
    return _catalog()
