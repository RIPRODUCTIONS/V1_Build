from __future__ import annotations

from typing import Annotated, Any

from app.db import get_db
from app.models import Task
from app.security.deps import require_scopes
from app.security.scopes import READ_RUNS, WRITE_RUNS
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

automation_router = APIRouter(prefix="/automation", tags=["automation:runs"])


@automation_router.get("/recent", dependencies=[Depends(require_scopes({READ_RUNS}))])
def recent_runs(db: Annotated[Session, Depends(get_db)], limit: int = 10) -> dict:
    rows = db.query(Task).order_by(Task.created_at.desc()).limit(max(1, min(50, limit))).all()
    items = [{"run_id": str(t.id), "status": t.status, "detail": None, "meta": {"intent": t.title}} for t in rows]
    return {"items": items}


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


