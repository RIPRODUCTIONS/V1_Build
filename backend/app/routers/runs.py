from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AgentRun, Artifact


router = APIRouter(prefix="/runs", tags=["runs"])
get_db_dep = Depends(get_db)


@router.get("")
def list_runs(
    status: str | None = None,
    intent: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort: str = "created_desc",
    db: Session = get_db_dep,
) -> dict[str, Any]:
    q = db.query(AgentRun)
    if status:
        q = q.filter(AgentRun.status == status)
    if intent:
        q = q.filter(AgentRun.intent == intent)
    q = q.order_by(
        AgentRun.created_at.desc() if sort == "created_desc" else AgentRun.created_at.asc()
    )
    rows = q.offset(offset).limit(limit).all()
    items = [
        {
            "id": r.id,
            "status": r.status,
            "created_at": r.created_at.isoformat() + "Z",
        }
        for r in rows
    ]
    return {"items": items}


@router.get("/{run_id}/artifacts")
def run_artifacts(run_id: int, db: Session = get_db_dep) -> dict[str, Any]:
    arts = db.query(Artifact).filter(Artifact.run_id == run_id).order_by(Artifact.id).all()
    items = [
        {
            "id": a.id,
            "kind": a.kind,
            "status": a.status,
            "file_path": a.file_path,
        }
        for a in arts
    ]
    return {"items": items}
