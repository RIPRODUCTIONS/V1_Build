from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import Annotated

from app.core.config import get_settings
from app.db import get_db
from app.models import AgentRun, Artifact, Lead, Task
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["admin"])
_logger = logging.getLogger("cleanup")

# Simple in-memory rate limiter: IP -> deque[timestamps]
_RATE_WINDOW_SECONDS = 60
_RATE_MAX_REQUESTS = 5
_ip_to_hits: dict[str, deque[float]] = defaultdict(deque)


def _get_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def require_rate_limit(request: Request) -> None:
    now = time.monotonic()
    ip = _get_ip(request)
    hits = _ip_to_hits[ip]
    # prune old entries
    while hits and now - hits[0] > _RATE_WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= _RATE_MAX_REQUESTS:
        _logger.info(
            "cleanup_request",
            extra={
                "ts": datetime.now(UTC).isoformat(),
                "ip": ip,
                "route": str(request.url.path),
                "auth": "rate_limited",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )
    hits.append(now)


def require_ci(
    request: Request, x_ci_token: Annotated[str | None, Header(alias="X-CI-Token")] = None
) -> None:
    settings = get_settings()
    ip = _get_ip(request)
    if not settings.ci_env:
        _logger.info(
            "cleanup_request",
            extra={
                "ts": datetime.now(UTC).isoformat(),
                "ip": ip,
                "route": str(request.url.path),
                "auth": "ci_env_false",
            },
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin cleanup disabled")
    if not settings.ci_cleanup_token or x_ci_token != settings.ci_cleanup_token:
        _logger.info(
            "cleanup_request",
            extra={
                "ts": datetime.now(UTC).isoformat(),
                "ip": ip,
                "route": str(request.url.path),
                "auth": "invalid_token",
            },
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    _logger.info(
        "cleanup_request",
        extra={
            "ts": datetime.now(UTC).isoformat(),
            "ip": ip,
            "route": str(request.url.path),
            "auth": "success",
        },
    )


@router.delete("/cleanup/leads", status_code=204)
def cleanup_leads(
    _: Annotated[None, Depends(require_ci)],
    __: Annotated[None, Depends(require_rate_limit)],
    db: Annotated[Session, Depends(get_db)],
):
    db.execute(delete(Lead))
    db.commit()


@router.delete("/cleanup/tasks", status_code=204)
def cleanup_tasks(
    _: Annotated[None, Depends(require_ci)],
    __: Annotated[None, Depends(require_rate_limit)],
    db: Annotated[Session, Depends(get_db)],
):
    db.execute(delete(Task))
    db.commit()


@router.delete("/cleanup/all", status_code=204)
def cleanup_all(
    _: Annotated[None, Depends(require_ci)],
    __: Annotated[None, Depends(require_rate_limit)],
    db: Annotated[Session, Depends(get_db)],
):
    # Order matters due to FKs
    db.execute(delete(Artifact))
    db.execute(delete(AgentRun))
    db.execute(delete(Task))
    db.execute(delete(Lead))
    # Users can also be removed if desired; keep default to retain admin user
    db.commit()
