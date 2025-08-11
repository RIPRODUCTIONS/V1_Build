from __future__ import annotations

import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationMiddleware(BaseHTTPMiddleware):
    HEADER_NAME = "X-Correlation-Id"

    async def dispatch(self, request: Request, call_next: Callable):
        corr = request.headers.get(self.HEADER_NAME)
        correlation_id = corr if corr else f"c-{uuid.uuid4().hex[:12]}"
        request.state.correlation_id = correlation_id
        response: Response = await call_next(request)
        response.headers[self.HEADER_NAME] = correlation_id
        return response



