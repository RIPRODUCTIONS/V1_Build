from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Annotated

from app.db import get_db
from app.models import OperatorEvent, OperatorRun
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/operator/runs", tags=["operator:runs"])


@router.get("/")
def list_runs(db: Annotated[Session, Depends(get_db)], limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    rows: list[OperatorRun] = (
        db.query(OperatorRun).order_by(OperatorRun.created_at.desc()).limit(limit).all()
    )
    return [
        {
            "id": r.id,
            "correlation_id": r.correlation_id,
            "description": r.description,
            "url": r.url,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/{correlation_id}")
def get_run(correlation_id: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    r = db.query(OperatorRun).filter(OperatorRun.correlation_id == correlation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "id": r.id,
        "correlation_id": r.correlation_id,
        "description": r.description,
        "url": r.url,
        "status": r.status,
        "created_at": r.created_at.isoformat(),
    }


@router.get("/{correlation_id}/events")
def get_run_events(correlation_id: str, db: Annotated[Session, Depends(get_db)], limit: int = Query(100, ge=1, le=500)) -> list[dict]:
    r = db.query(OperatorRun).filter(OperatorRun.correlation_id == correlation_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    evs = (
        db.query(OperatorEvent)
        .filter(OperatorEvent.run_id == r.id)
        .order_by(OperatorEvent.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "payload": e.payload,
            "created_at": e.created_at.isoformat(),
        }
        for e in evs
    ]


@router.get("/{correlation_id}/stream")
async def stream_run_events(correlation_id: str, db: Annotated[Session, Depends(get_db)]) -> StreamingResponse:
    run = db.query(OperatorRun).filter(OperatorRun.correlation_id == correlation_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="run not found")

    async def event_generator() -> AsyncGenerator[bytes, None]:
        last_id = 0
        # Initial catch-up
        for e in (
            db.query(OperatorEvent)
            .filter(OperatorEvent.run_id == run.id)
            .order_by(OperatorEvent.id.asc())
            .limit(100)
            .all()
        ):
            last_id = e.id
            yield f"data: {e.payload}\n\n".encode()
        # Poll loop
        while True:
            await asyncio.sleep(1)
            new = (
                db.query(OperatorEvent)
                .filter(OperatorEvent.run_id == run.id, OperatorEvent.id > last_id)
                .order_by(OperatorEvent.id.asc())
                .all()
            )
            for e in new:
                last_id = e.id
                yield f"data: {e.payload}\n\n".encode()
            # Heartbeat
            if not new:
                yield b": keep-alive\n\n"

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


