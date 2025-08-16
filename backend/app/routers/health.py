from __future__ import annotations

from contextlib import suppress

from app.db import engine
from app.core.config import get_settings
from app.agent.celery_app import celery_app
from app.selfheal.services import HealthMonitor  # type: ignore
from fastapi import APIRouter
from sqlalchemy import text

# Public health router, mounted under /api and legacy root
health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("")
async def health_root():
    return {"status": "ok"}


@health_router.get("/dependency_status")
async def check_dependency_status():
    # DB
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    # Redis
    redis_ok = False
    try:
        import redis  # type: ignore
        r = redis.from_url(get_settings().REDIS_URL)
        try:
            redis_ok = bool(r.ping())
        finally:
            r.close()
    except Exception:
        redis_ok = False
    return {"db": "ok" if db_ok else "fail", "redis": "ok" if redis_ok else "fail", "external": "skipped"}


@health_router.get("/live")
async def health_live():
    return {"status": "alive"}


@health_router.get("/ready")
async def health_ready():
    db_ok = False
    redis_ok = False
    # Check DB
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    # Check Redis
    try:
        import redis  # type: ignore
        r = redis.from_url(get_settings().REDIS_URL)
        try:
            redis_ok = bool(r.ping())
        finally:
            r.close()
    except Exception:
        redis_ok = False

    status = "ready" if (db_ok and redis_ok) else "not_ready"
    return {"status": status, "db": "ok" if db_ok else "fail", "redis": "ok" if redis_ok else "fail"}


@health_router.get("/system_metrics")
async def get_system_metrics():
    return {"metrics": "skipped"}


@health_router.get("/celery_status")
async def celery_status():
    # Ping workers
    worker_ok = False
    try:
        res = celery_app.control.ping(timeout=1.0)
        worker_ok = bool(res)
    except Exception:
        worker_ok = False
    # Queue depths (best-effort for Redis transport)
    queues: dict[str, int | None] = {"default": None, "automations": None, "webexec": None}
    try:
        import redis  # type: ignore
        r = redis.from_url(get_settings().REDIS_URL)
        try:
            for q in list(queues.keys()):
                try:
                    queues[q] = int(r.llen(q))
                except Exception:
                    queues[q] = None
        finally:
            r.close()
    except Exception:
        pass
    return {"worker_ok": worker_ok, "queues": queues}


@health_router.get("/selfheal_status")
async def selfheal_status():
    """Read-only self-heal status snapshot.

    Runs the HealthMonitor checks once and summarizes component health.
    """
    try:
        monitor = HealthMonitor()
        items = await monitor.check_all_components()
        summary = {
            "components": [
                {
                    "component": it.component,
                    "score": it.health_score,
                    "issues": list(it.issues or []),
                    "last_check": getattr(it.last_check, "isoformat", lambda: None)(),
                }
                for it in items
            ],
            "issues_total": sum(1 for it in items if (it.issues or [])),
        }
        return summary
    except Exception as exc:  # pragma: no cover
        return {"components": [], "issues_total": 0, "error": str(exc)}


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
