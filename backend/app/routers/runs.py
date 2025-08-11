from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi import HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.dependencies.auth import require_scope_hs256
from app.models import AgentRun, Artifact


router = APIRouter(prefix="/runs", tags=["runs"])
get_db_dep = Depends(get_db)


@router.get("")
def list_runs(
    db: Session = get_db_dep,
    page_limit: int = Query(default=50, ge=1, le=1000),
    page_offset: int = Query(default=0, ge=0),
    sort: str = Query(default="created_desc"),
    status: str | None = Query(default=None),
    intent: str | None = Query(default=None),
) -> dict[str, Any]:
    # Optional read RBAC when SECURE_MODE is enabled
    if get_settings().SECURE_MODE:
        require_scope_hs256("life.read")(None)  # dependency-style call; header enforced by FastAPI normally
    q = db.query(AgentRun)
    if status:
        q = q.filter(AgentRun.status == status)
    if intent:
        q = q.filter(AgentRun.intent == intent)
    q = q.order_by(
        AgentRun.created_at.desc() if sort == "created_desc" else AgentRun.created_at.asc()
    )
    rows = q.offset(page_offset).limit(page_limit).all()
    items = [
        {
            "id": r.id,
            "status": r.status,
            "created_at": r.created_at.isoformat() + "Z",
        }
        for r in rows
    ]
    return {"items": items}


@router.get("/{run_id}")
def get_run(run_id: int, db: Session = get_db_dep) -> dict[str, Any]:
    if get_settings().SECURE_MODE:
        require_scope_hs256("life.read")(None)
    r = db.get(AgentRun, run_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return {
        "id": r.id,
        "status": r.status,
        "intent": r.intent,
        "department": r.department,
        "created_at": r.created_at.isoformat() + "Z",
    }


@router.get("/{run_id}/artifacts")
def run_artifacts(run_id: int, db: Session = get_db_dep) -> dict[str, Any]:
    if get_settings().SECURE_MODE:
        require_scope_hs256("life.read")(None)
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
