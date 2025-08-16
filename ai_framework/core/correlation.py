from __future__ import annotations

import contextvars
import time
import uuid
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="")
request_ts_var: contextvars.ContextVar[float] = contextvars.ContextVar("request_ts", default=0.0)


def get_correlation_id() -> str:
    cid = correlation_id_var.get()
    if not cid:
        cid = new_correlation_id()
        correlation_id_var.set(cid)
    return cid


def new_correlation_id() -> str:
    return f"atomic-{uuid.uuid4().hex[:8]}-{int(time.time())}"


def attach_correlation(data: dict[str, Any]) -> dict[str, Any]:
    d = dict(data)
    d["correlation_id"] = get_correlation_id()
    return d


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        cid = request.headers.get("X-Correlation-Id") or new_correlation_id()
        correlation_id_var.set(cid)
        request_ts_var.set(time.time())
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = cid
        return response







