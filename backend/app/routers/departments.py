from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix='/departments', tags=['departments'])


def _catalog() -> dict[str, Any]:
    """Load catalog, tolerating missing files and legacy shapes.

    Legacy variants observed:
      - { "departments": ["ops", ...], "tasks": [{"id":..., "department":...}] }
      - { "departments": [{"name": "ops", "tasks": [{"key": "..."}]}] }
    """
    p = Path(__file__).resolve().parents[3] / 'platform' / 'shared' / 'catalog' / 'tasks.json'
    if not p.exists():
        return {"departments": [], "tasks": []}
    data = json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        return {"departments": [], "tasks": []}
    # Normalize departments to list of names
    depts_raw = data.get('departments', [])
    dept_names: list[str] = []
    if isinstance(depts_raw, list):
        for d in depts_raw:
            if isinstance(d, str):
                dept_names.append(d)
            elif isinstance(d, dict) and 'name' in d:
                dept_names.append(str(d['name']))
    # Normalize tasks to flat list
    tasks: list[dict[str, Any]] = []
    if isinstance(data.get('tasks'), list):
        tasks = [t for t in data['tasks'] if isinstance(t, dict)]
    else:
        # derive from nested departments shape
        if isinstance(depts_raw, list):
            for d in depts_raw:
                if isinstance(d, dict):
                    for t in d.get('tasks', []) or []:
                        if isinstance(t, dict):
                            tasks.append({
                                'id': t.get('key') or t.get('id'),
                                'department': d.get('name'),
                                **t,
                            })
    return {"departments": dept_names, "tasks": tasks}


@router.get('/')
def list_departments() -> dict[str, Any]:
    data = _catalog()
    # Back-compat: tests expect items to be a list of department names containing 'life' and 'finance'
    return {'items': data.get('departments', [])}


@router.get('/tasks/catalog')
def tasks_catalog() -> dict[str, Any]:
    data = _catalog()
    # Back-compat: include both tasks and departments keys
    return {'tasks': data.get('tasks', []), 'departments': data.get('departments', [])}
