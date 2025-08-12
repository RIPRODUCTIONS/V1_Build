from __future__ import annotations

import os
from collections.abc import Callable, Iterable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class InternalTokenGuard(BaseHTTPMiddleware):
    def __init__(self, app, path_prefixes: Iterable[str] | None = None) -> None:
        super().__init__(app)
        self.secure_mode = os.getenv('SECURE_MODE', '').lower() in {'1', 'true', 'yes', 'on'}
        self.internal_token = os.getenv('INTERNAL_TOKEN', '')
        self.path_prefixes = tuple(path_prefixes or ('/cursor', '/ops'))

    async def dispatch(self, request: Request, call_next: Callable):
        if self.secure_mode and request.url.path.startswith(self.path_prefixes):
            header = request.headers.get('X-Internal-Token', '')
            if not self.internal_token or header != self.internal_token:
                return JSONResponse({'detail': 'Forbidden'}, status_code=403)
        return await call_next(request)
