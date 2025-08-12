import json

from starlette.types import ASGIApp, Receive, Scope, Send


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = 2_000_000) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        total = 0

        async def limited_receive() -> dict:
            nonlocal total
            message = await receive()
            if message.get("type") == "http.request":
                body = message.get("body", b"") or b""
                total += len(body)
                if total > self.max_bytes:
                    start = {
                        "type": "http.response.start",
                        "status": 413,
                        "headers": [(b"content-type", b"application/json")],
                    }
                    await send(start)
                    await send(
                        {
                            "type": "http.response.body",
                            "body": json.dumps({"detail": "Request entity too large"}).encode("utf-8"),
                        }
                    )
                    return {"type": "http.disconnect"}
            return message

        return await self.app(scope, limited_receive, send)


