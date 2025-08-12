from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Path

from app.security.deps import require_scopes
from app.security.scopes import READ_RUNS, WRITE_RUNS


router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get(
    "",
    dependencies=[Depends(require_scopes({READ_RUNS}))],
)
async def list_runs() -> dict[str, Any]:
    # Minimal placeholder to exercise RBAC; wire to real data later
    return {"items": [], "total": 0}


@router.post(
    "",
    dependencies=[Depends(require_scopes({WRITE_RUNS}))],
)
async def create_run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = payload
    return {"id": 1}


@router.get(
    "/{run_id}",
    dependencies=[Depends(require_scopes({READ_RUNS}))],
)
async def get_run(run_id: int = Path(...)) -> dict[str, Any]:
    return {"id": run_id}


@router.patch(
    "/{run_id}",
    dependencies=[Depends(require_scopes({WRITE_RUNS}))],
)
async def update_run(run_id: int, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = payload
    return {"id": run_id, "ok": True}


@router.delete(
    "/{run_id}",
    dependencies=[Depends(require_scopes({WRITE_RUNS}))],
)
async def delete_run(run_id: int) -> dict[str, Any]:
    return {"id": run_id, "ok": True}


