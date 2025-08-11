from __future__ import annotations

import json
import time
from typing import Any

from app.db import get_db
from app.dependencies.auth import require_scope_hs256
from app.models import AgentRun, Artifact
from app.services.queue.redis_bus import RedisEventBus
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/research", tags=["research"])

# Initialize Redis event bus
event_bus = RedisEventBus(stream="events", consumer_group="research_group")


@router.post("/market-gaps/run")
async def run_market_gap_scanner(
    db: Session = Depends(get_db), subject: str = Depends(require_scope_hs256("research.read"))
) -> dict[str, Any]:
    """Run the Market Gap Scanner to identify business opportunities."""

    try:
        # Create run record
        run = AgentRun(
            owner_id=1,  # TODO: Get from auth context
            status="started",
            intent="research.market_gap_scanner",
            department="research",
            correlation_id=f"research_{int(time.time())}",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Emit automation event
        event = {
            "event_type": "automation.run.requested",
            "run_id": str(run.id),
            "intent": "research.market_gap_scanner",
            "department": "research",
            "correlation_id": run.correlation_id,
            "subject": subject,
            "timestamp": time.time(),
        }

        event_bus.publish(event)

        return {
            "run_id": str(run.id),
            "status": "started",
            "intent": "research.market_gap_scanner",
            "department": "research",
            "correlation_id": run.correlation_id,
            "message": "Market gap scanner started successfully",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start market gap scanner: {str(e)}",
        ) from e


@router.get("/market-gaps/results")
async def get_market_gap_results(
    db: Session = Depends(get_db), subject: str = Depends(require_scope_hs256("research.read"))
) -> dict[str, Any]:
    """Get results from market gap scanner runs."""

    try:
        # Get recent research runs
        runs = (
            db.query(AgentRun)
            .filter(
                AgentRun.intent == "research.market_gap_scanner", AgentRun.department == "research"
            )
            .order_by(AgentRun.created_at.desc())
            .limit(10)
            .all()
        )

        results = []
        for run in runs:
            # Get artifacts for this run
            artifacts = db.query(Artifact).filter(Artifact.run_id == run.id).all()

            run_data = {
                "run_id": str(run.id),
                "status": run.status,
                "created_at": run.created_at.isoformat() + "Z",
                "correlation_id": run.correlation_id,
                "artifacts": [
                    {
                        "id": artifact.id,
                        "kind": artifact.kind,
                        "status": artifact.status,
                        "file_path": artifact.file_path,
                    }
                    for artifact in artifacts
                ],
            }
            results.append(run_data)

        return {"results": results, "total": len(results)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market gap results: {str(e)}",
        ) from e


@router.get("/market-gaps/latest")
async def get_latest_market_gaps(
    db: Session = Depends(get_db), subject: str = Depends(require_scope_hs256("research.read"))
) -> dict[str, Any]:
    """Get the latest market gap analysis results."""

    try:
        # Get the most recent completed run
        latest_run = (
            db.query(AgentRun)
            .filter(
                AgentRun.intent == "research.market_gap_scanner",
                AgentRun.department == "research",
                AgentRun.status == "completed",
            )
            .order_by(AgentRun.created_at.desc())
            .first()
        )

        if not latest_run:
            return {"message": "No completed market gap scans found", "results": []}

        # Get artifacts for this run
        artifacts = db.query(Artifact).filter(Artifact.run_id == latest_run.id).all()

        # Parse artifact content to extract market gaps
        market_gaps = []
        for artifact in artifacts:
            if artifact.kind == "market_gaps" and artifact.content:
                try:
                    gap_data = json.loads(artifact.content)
                    if isinstance(gap_data, list):
                        market_gaps.extend(gap_data)
                    elif isinstance(gap_data, dict) and "gaps" in gap_data:
                        market_gaps.extend(gap_data["gaps"])
                except json.JSONDecodeError:
                    continue

        return {
            "run_id": str(latest_run.id),
            "scanned_at": latest_run.created_at.isoformat() + "Z",
            "correlation_id": latest_run.correlation_id,
            "market_gaps": market_gaps[:10],  # Top 10 results
            "total_gaps": len(market_gaps),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest market gaps: {str(e)}",
        ) from e


@router.get("/status")
async def get_research_status(
    db: Session = Depends(get_db), subject: str = Depends(require_scope_hs256("research.read"))
) -> dict[str, Any]:
    """Get overall research department status."""

    try:
        # Count runs by status
        status_counts = (
            db.query(AgentRun.status, db.func.count(AgentRun.id))
            .filter(AgentRun.department == "research")
            .group_by(AgentRun.status)
            .all()
        )

        # Get recent activity
        recent_runs = (
            db.query(AgentRun)
            .filter(AgentRun.department == "research")
            .order_by(AgentRun.created_at.desc())
            .limit(5)
            .all()
        )

        return {
            "department": "research",
            "status_summary": dict(status_counts),
            "recent_activity": [
                {
                    "run_id": str(run.id),
                    "intent": run.intent,
                    "status": run.status,
                    "created_at": run.created_at.isoformat() + "Z",
                }
                for run in recent_runs
            ],
            "total_runs": sum(count for _, count in status_counts),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get research status: {str(e)}",
        ) from e
