from __future__ import annotations

import asyncio
import functools
import random
from collections.abc import Awaitable, Callable
from typing import Any

import httpx


def retry_with_circuit_breaker(max_retries: int = 3, backoff_multiplier: float = 2.0, circuit_breaker_threshold: int = 5):
    """Decorator for retrying async Google API calls with simple circuit breaker.

    - Retries on 429 and 5xx with exponential backoff + jitter.
    - On 401/403, relies on caller to refresh token; if raised again, aborts.
    - Opens circuit after threshold consecutive failures; half-open after cool-down.
    """

    def decorator(func: Callable[..., Awaitable[Any]]):
        failure_count = 0
        circuit_open = False
        last_open_ts = 0.0

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal failure_count, circuit_open, last_open_ts
            # Half-open every 30s
            if circuit_open and (asyncio.get_event_loop().time() - last_open_ts < 30.0):
                raise RuntimeError("circuit_open")
            circuit_open = False
            delay = 0.5
            for attempt in range(max_retries + 1):
                try:
                    res = await func(*args, **kwargs)
                    failure_count = 0
                    return res
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    if status == 429 or 500 <= status < 600:
                        if attempt < max_retries:
                            await asyncio.sleep(delay + random.uniform(0, delay * 0.2))
                            delay *= backoff_multiplier
                            continue
                        failure_count += 1
                    elif status in (401, 403):
                        # Let caller handle token refresh; no blind retries beyond first
                        failure_count += 1
                    else:
                        failure_count += 1
                    if failure_count >= circuit_breaker_threshold:
                        circuit_open = True
                        last_open_ts = asyncio.get_event_loop().time()
                    raise
                except Exception:
                    failure_count += 1
                    if failure_count >= circuit_breaker_threshold:
                        circuit_open = True
                        last_open_ts = asyncio.get_event_loop().time()
                    raise

        return wrapper

    return decorator


