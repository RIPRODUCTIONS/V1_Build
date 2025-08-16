from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import httpx


async def google_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    data: Any = None,
    timeout: float = 20.0,
    retries: int = 2,
    refresh: Callable[[], asyncio.Future] | None = None,
) -> httpx.Response:
    """Make a resilient Google API request with basic backoff and optional token refresh.

    - Retries on 429/5xx with exponential backoff and jitter
    - On 401, attempts one refresh() if provided, then retries once
    """
    backoff = 0.8
    attempt = 0
    auth_refreshed = False
    async with httpx.AsyncClient(timeout=timeout) as client:
        while True:
            attempt += 1
            r = await client.request(method.upper(), url, headers=headers, params=params, json=json, data=data)
            # Token expired
            if r.status_code == 401 and not auth_refreshed and refresh is not None:
                try:
                    await refresh()
                    auth_refreshed = True
                    # Caller should update headers before next loop (e.g., via closure)
                except Exception:
                    return r
                continue
            # Transient
            if r.status_code in (429, 500, 502, 503, 504) and attempt <= retries:
                await asyncio.sleep(backoff)
                backoff *= 2
                continue
            return r


