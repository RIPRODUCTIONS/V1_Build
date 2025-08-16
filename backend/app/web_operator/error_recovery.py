from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


async def retry_async(
    fn: Callable[[], Awaitable[Any]],
    retries: int = 3,
    base_delay_s: float = 0.5,
) -> Any:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            return await fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            await asyncio.sleep(base_delay_s * (2**attempt))
    if last_exc:
        raise last_exc
    raise RuntimeError("retry_async failed without exception")


async def with_fallbacks(primary: Callable[[], Awaitable[Any]], *fallbacks: Callable[[], Awaitable[Any]]) -> Any:
    try:
        return await primary()
    except Exception:
        for fb in fallbacks:
            try:
                return await fb()
            except Exception:
                continue
        raise


