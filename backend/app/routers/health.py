from __future__ import annotations

from contextlib import suppress

from app.db import engine
from fastapi import APIRouter
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/healthz")
def healthz():
    return {"status": "ok"}


@router.get("/readyz")
def readyz():
    # Basic DB connectivity check
    try:
        with engine.connect() as conn, suppress(Exception):
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:  # pragma: no cover - readiness failure path
        return {"status": "not_ready", "detail": str(exc)}
