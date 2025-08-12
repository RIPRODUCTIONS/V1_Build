from __future__ import annotations

import sys
import traceback

from starlette.middleware.base import BaseHTTPMiddleware


class BootLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log any uncaught errors during startup/request processing."""

    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception:
            print('🚨 UNCAUGHT ERROR in BootLogMiddleware:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            raise
