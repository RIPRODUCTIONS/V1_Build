from __future__ import annotations

import threading
import time


class TokenBucket:
    def __init__(self, rate_per_s: float, capacity: float | None = None) -> None:
        self.rate = float(max(rate_per_s, 0.0001))
        self.capacity = float(capacity if capacity is not None else self.rate)
        self._tokens = self.capacity
        self._last = time.monotonic()
        self._lock = threading.Lock()
        self._drops = 0

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        self._last = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)

    def allow(self) -> bool:
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            self._drops += 1
            return False

    def wait(self) -> None:
        # Blocking helper (used by CLI only)
        while True:
            if self.allow():
                return
            time.sleep(0.05)

    def stats(self) -> dict:
        with self._lock:
            return {
                "capacity": self.capacity,
                "rate_per_s": self.rate,
                "tokens": self._tokens,
                "drops": self._drops,
            }
