from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

try:
    # If you already have a correlation middleware util, use it:
    from app.middleware.correlation import get_correlation_id  # type: ignore
except Exception:

    def get_correlation_id() -> str | None:  # fallback
        return None


class ErrorEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            return JSONResponse(
                {
                    'ok': False,
                    'error': {'type': type(e).__name__, 'message': str(e)},
                    'correlation_id': get_correlation_id(),
                },
                status_code=500,
            )
