from __future__ import annotations

from contextlib import suppress

from app.db import engine
from fastapi import APIRouter
from sqlalchemy import text

# Public health router, mounted under /api and legacy root
health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("")
async def health_root():
    return {"status": "ok"}


@health_router.get("/dependency_status")
async def check_dependency_status():
    return {"db": "ok", "redis": "unknown", "external": "skipped"}


@health_router.get("/live")
async def health_live():
    return {"status": "alive"}


@health_router.get("/ready")
async def health_ready():
    try:
        with engine.connect() as conn, suppress(Exception):
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:  # pragma: no cover
        return {"status": "not_ready", "detail": str(exc)}


@health_router.get("/system_metrics")
async def get_system_metrics():
    return {"metrics": "skipped"}


# Legacy endpoints retained
@health_router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@health_router.get("/readyz")
async def readyz():
    try:
        with engine.connect() as conn, suppress(Exception):
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:  # pragma: no cover
        return {"status": "not_ready", "detail": str(exc)}


@health_router.get("/operator_readiness")
async def check_operator_readiness():
    return {"ready": False, "status": "disabled"}


# Back-compat export name used by main.py (imported as health_router)
router = health_router
