from __future__ import annotations

import hashlib
import json
from contextlib import suppress
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.automation.state import get_status, list_recent
from app.db import get_db
from app.dependencies.auth import optional_require_life_read
from app.models import AgentRun, Artifact
from app.obs.run_logger import run_logger

router = APIRouter(prefix='', tags=['runs'])
get_db_dep = Depends(get_db)
optional_life_read_dep = Depends(optional_require_life_read)


class RunOut(BaseModel):
    id: str
    intent: str
    status: str
    created_at: datetime
    updated_at: datetime
    detail: dict | None = None


@router.get('/runs')
async def list_runs(
    response: Response,
    intent: str | None = Query(None, description='Filter by intent'),
    status: str | None = Query(
        None, regex='^(queued|running|succeeded|failed)$', description='Filter by status'
    ),
    from_ts: str | None = Query(
        None, alias='from', description='Filter from timestamp (ISO format)'
    ),
    to_ts: str | None = Query(None, alias='to', description='Filter to timestamp (ISO format)'),
    limit: int = Query(25, ge=1, le=100, description='Number of runs to return'),
    offset: int = Query(0, ge=0, description='Offset for pagination'),
    sort: str | None = Query(None, description='Sort order, e.g., created_desc'),
    cursor: str | None = Query(None, description='Cursor for pagination (created_at|id format)'),
    _: str | None = optional_life_read_dep,
):
    """List automation runs with filtering and pagination."""
    try:
        # Parse timestamps if provided
        from_dt = None
        to_dt = None
        if from_ts:
            with suppress(ValueError):
                from_dt = datetime.fromisoformat(from_ts.replace('Z', '+00:00'))
        if to_ts:
            with suppress(ValueError):
                to_dt = datetime.fromisoformat(to_ts.replace('Z', '+00:00'))

        # Get recent runs (this will need to be enhanced for proper filtering)
        runs_data = await list_recent(limit)

        # Apply filters
        filtered_runs = []
        for run in runs_data:
            # Filter by intent
            if intent and run.get('detail', {}).get('intent') != intent:
                continue

            # Filter by status
            if status and run.get('status') != status:
                continue

            # Filter by timestamp range
            if from_dt or to_dt:
                run_ts = run.get('ts')
                if run_ts:
                    run_dt = datetime.fromtimestamp(run_ts)
                    if from_dt and run_dt < from_dt:
                        continue
                    if to_dt and run_dt > to_dt:
                        continue

            # Convert to RunOut format
            run_out = RunOut(
                id=run.get('run_id', ''),
                intent=run.get('detail', {}).get('intent', ''),
                status=run.get('status', ''),
                created_at=datetime.fromtimestamp(run.get('ts', 0))
                if run.get('ts')
                else datetime.now(),
                updated_at=datetime.fromtimestamp(run.get('ts', 0))
                if run.get('ts')
                else datetime.now(),
                detail=run.get('detail'),
            )
            filtered_runs.append(run_out)

        # Apply cursor-based pagination if cursor provided
        if cursor:
            try:
                created_at_str, _, rid = cursor.partition('|')
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))

                # Filter runs created before the cursor
                filtered_runs = [
                    run
                    for run in filtered_runs
                    if (run.created_at < created_at)
                    or (run.created_at == created_at and run.id < rid)
                ]
            except (ValueError, IndexError):
                # Invalid cursor, return empty
                filtered_runs = []

        # Limit results
        # Offset/slice
        filtered_runs = filtered_runs[offset : offset + limit]

        # Add caching headers
        payload_items = [run.model_dump() for run in filtered_runs]
        body = json.dumps(payload_items, separators=(',', ':'), default=str)
        etag = hashlib.md5(body.encode()).hexdigest()
        response.headers['ETag'] = etag
        response.headers['Cache-Control'] = 'public, max-age=10'

        # Back-compat shape expected by legacy tests
        return {'items': payload_items, 'total': len(payload_items)}

    except Exception as e:
        # Log error and return empty list
        print(f'Error in list_runs: {e}')
        return []


@router.get('/runs/{run_id}')
async def get_run_detail(run_id: str, _: str | None = optional_life_read_dep):
    """Get detailed information about a specific run."""
    try:
        run_data = await get_status(run_id)
        if not run_data:
            return {'error': 'Run not found'}
        return {'run_id': run_id, **run_data}
    except Exception as e:
        return {'error': f'Failed to get run: {str(e)}'}


@router.get('/runs/{run_id}/artifacts')
def run_artifacts(
    run_id: int,
    db: Session = get_db_dep,
    _: str | None = optional_life_read_dep,
    request: Request = None,
) -> dict[str, Any]:
    """Get artifacts for a specific automation run."""
    r = db.get(AgentRun, run_id)
    if not r:
        correlation_id = getattr(request.state, 'correlation_id', None) if request else None
        detail = {'error': 'not_found'}
        if correlation_id:
            detail['correlation_id'] = correlation_id
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    arts = db.query(Artifact).filter(Artifact.run_id == run_id).order_by(Artifact.id).all()
    items = [
        {
            'id': a.id,
            'kind': a.kind,
            'status': a.status,
            'file_path': a.file_path,
        }
        for a in arts
    ]

    # Log the artifacts access
    run_logger.log_run_event(
        run_id=str(run_id),
        event_type='run.artifacts',
        status='accessed',
        correlation_id=r.correlation_id,
        intent=r.intent,
        department=r.department,
        metadata={'artifact_count': len(items)},
    )

    return {'items': items}
