from __future__ import annotations

from typing import Any

from app.db import get_db
from app.dependencies.auth import require_runs_read_scope, require_runs_write_scope
from app.models import AgentRun, Artifact
from app.obs.run_logger import run_logger
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/runs", tags=["runs"])
get_db_dep = Depends(get_db)


@router.get("/")
def list_runs(  # noqa: PLR0913
    db: Session = get_db_dep,
    page_limit: int = Query(default=50, ge=1, le=1000),
    page_offset: int = Query(default=0, ge=0),
    sort: str = Query(default="created_desc"),
    status: str | None = Query(default=None),
    intent: str | None = Query(default=None),
    department: str | None = Query(default=None),
    correlation_id: str | None = Query(default=None),
    subject: str = Depends(require_runs_read_scope),
) -> dict[str, Any]:
    """List automation runs with filtering and pagination."""
    q = db.query(AgentRun)

    # Apply filters
    if status:
        q = q.filter(AgentRun.status == status)
    if intent:
        q = q.filter(AgentRun.intent == intent)
    if department:
        q = q.filter(AgentRun.department == department)
    if correlation_id:
        q = q.filter(AgentRun.correlation_id == correlation_id)

    # Apply sorting
    if sort == "created_desc":
        q = q.order_by(AgentRun.created_at.desc())
    elif sort == "created_asc":
        q = q.order_by(AgentRun.created_at.asc())
    elif sort == "status":
        q = q.order_by(AgentRun.status, AgentRun.created_at.desc())
    elif sort == "intent":
        q = q.order_by(AgentRun.intent, AgentRun.created_at.desc())
    else:
        q = q.order_by(AgentRun.created_at.desc())

    rows = q.offset(page_offset).limit(page_limit).all()
    items = [
        {
            "run_id": str(r.id),
            "status": r.status,
            "intent": r.intent or "N/A",
            "department": r.department or "N/A",
            "correlation_id": r.correlation_id or "N/A",
            "created_at": r.created_at.isoformat() + "Z",
        }
        for r in rows
    ]

    # Log the query for audit
    run_logger.log_run_event(
        run_id="query",
        event_type="runs.list",
        status="success",
        metadata={
            "filters": {
                "status": status,
                "intent": intent,
                "department": department,
                "correlation_id": correlation_id,
            },
            "pagination": {"limit": page_limit, "offset": page_offset},
            "sort": sort,
            "count": len(items),
        },
    )

    return {"items": items}


@router.get("/{run_id}")
def get_run(
    run_id: int,
    db: Session = get_db_dep,
    subject: str = Depends(require_runs_read_scope),
    request: Request = None,
) -> dict[str, Any]:
    """Get details of a specific automation run."""
    r = db.get(AgentRun, run_id)
    if not r:
        correlation_id = getattr(request.state, "correlation_id", None) if request else None
        detail = {"error": "not_found"}
        if correlation_id:
            detail["correlation_id"] = correlation_id
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    # Log the access
    run_logger.log_run_event(
        run_id=str(run_id),
        event_type="run.detail",
        status="accessed",
        correlation_id=r.correlation_id,
        intent=r.intent,
        department=r.department,
    )

    return {
        "run_id": str(r.id),
        "status": r.status,
        "intent": r.intent,
        "department": r.department,
        "correlation_id": r.correlation_id,
        "created_at": r.created_at.isoformat() + "Z",
    }


@router.patch("/{run_id}")
def update_run(
    run_id: int,
    status: str | None = None,
    intent: str | None = None,
    department: str | None = None,
    correlation_id: str | None = None,
    db: Session = get_db_dep,
    subject: str = Depends(require_runs_write_scope),
    request: Request = None,
) -> dict[str, Any]:
    """Update run status and metadata (internal use only)."""
    r = db.get(AgentRun, run_id)
    if not r:
        req_correlation_id = getattr(request.state, "correlation_id", None) if request else None
        detail = {"error": "not_found"}
        if req_correlation_id:
            detail["correlation_id"] = req_correlation_id
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    # Validate status if provided
    if status and status not in ["pending", "started", "completed", "failed", "cancelled"]:
        req_correlation_id = getattr(request.state, "correlation_id", None) if request else None
        detail = {
            "error": f"Invalid status: {status}. Must be one of: pending, started, completed, failed, cancelled"
        }
        if req_correlation_id:
            detail["correlation_id"] = req_correlation_id
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    # Track what's being updated
    updates = {}
    if status is not None:
        updates["status"] = status
        r.status = status
    if intent is not None:
        updates["intent"] = intent
        r.intent = intent
    if department is not None:
        updates["department"] = department
        r.department = department
    if correlation_id is not None:
        updates["correlation_id"] = correlation_id
        r.correlation_id = correlation_id

    if updates:
        db.add(r)
        db.commit()

        # Log the update
        run_logger.log_run_status_update(
            run_id=str(run_id),
            status=r.status,
            correlation_id=r.correlation_id,
            intent=r.intent,
            department=r.department,
            metadata={"updates": updates},
        )

    return {
        "ok": True,
        "run_id": str(run_id),
        "updated": updates,
        "current": {
            "status": r.status,
            "intent": r.intent,
            "department": r.department,
            "correlation_id": r.correlation_id,
        },
    }


@router.get("/{run_id}/artifacts")
def run_artifacts(
    run_id: int,
    db: Session = get_db_dep,
    subject: str = Depends(require_runs_read_scope),
    request: Request = None,
) -> dict[str, Any]:
    """Get artifacts for a specific automation run."""
    r = db.get(AgentRun, run_id)
    if not r:
        correlation_id = getattr(request.state, "correlation_id", None) if request else None
        detail = {"error": "not_found"}
        if correlation_id:
            detail["correlation_id"] = correlation_id
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

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

    # Log the artifacts access
    run_logger.log_run_event(
        run_id=str(run_id),
        event_type="run.artifacts",
        status="accessed",
        correlation_id=r.correlation_id,
        intent=r.intent,
        department=r.department,
        metadata={"artifact_count": len(items)},
    )

    return {"items": items}
