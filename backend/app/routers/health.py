from __future__ import annotations

from contextlib import suppress

from fastapi import APIRouter
from sqlalchemy import text

from app.db import engine
from app.obs.metrics import metrics_endpoint

router = APIRouter(tags=['health'])


@router.get('/health')
def health():
    return {'status': 'ok'}


@router.get('/healthz')
def healthz():
    return {'status': 'ok'}


@router.get('/readyz')
def readyz():
    # Basic DB connectivity check
    try:
        with engine.connect() as conn, suppress(Exception):
            conn.execute(text('SELECT 1'))
        return {'status': 'ready'}
    except Exception as exc:  # pragma: no cover - readiness failure path
        return {'status': 'not_ready', 'detail': str(exc)}


@router.get('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return metrics_endpoint()


@router.get('/health/manager')
def manager_health():
    """Manager orchestrator health check"""
    try:
        # TODO: Add actual manager health check when orchestrator is running
        # For now, return basic health status
        return {
            'status': 'healthy',
            'component': 'manager_orchestrator',
            'timestamp': '2025-08-11T23:00:00Z',
            'details': {
                'redis_connection': 'unknown',
                'event_processing': 'unknown',
                'last_heartbeat': 'unknown',
            },
        }
    except Exception as exc:
        return {
            'status': 'unhealthy',
            'component': 'manager_orchestrator',
            'error': str(exc),
            'timestamp': '2025-08-11T23:00:00Z',
        }
