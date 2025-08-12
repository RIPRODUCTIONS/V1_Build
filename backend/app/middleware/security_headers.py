from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import get_settings


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, csp_report_only: bool = True) -> None:
        self.app = app
        self.csp_report_only = csp_report_only
        self.settings = get_settings()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def _send(event):
            if event.get("type") == "http.response.start":
                headers = list(event.get("headers", []))

                def add(k: str, v: str) -> None:
                    headers.append((k.encode("utf-8"), v.encode("utf-8")))

                add("x-content-type-options", "nosniff")
                add("referrer-policy", "strict-origin-when-cross-origin")
                add("x-frame-options", "DENY")
                add("permissions-policy", "camera=(), microphone=(), geolocation=()")

                if self.settings.SECURE_MODE:
                    add("strict-transport-security", "max-age=31536000; includeSubDomains; preload")

                csp = (
                    "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                    "script-src 'self'; frame-ancestors 'none'"
                )
                name = (
                    "content-security-policy-report-only" if self.csp_report_only else "content-security-policy"
                )
                add(name, csp)

                event["headers"] = headers
            await send(event)

        await self.app(scope, receive, _send)


