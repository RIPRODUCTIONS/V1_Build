from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0


class TTLCache:
    def __init__(self, max_items: int, ttl_s: int) -> None:
        self.max_items = max_items
        self.ttl_s = ttl_s
        self._lock = threading.Lock()
        self._data: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._stats = CacheStats()

    def _evict_if_needed(self) -> None:
        while len(self._data) > self.max_items:
            self._data.popitem(last=False)
            self._stats.evictions += 1

    def get(self, key: str) -> Any | None:
        now = time.time()
        with self._lock:
            item = self._data.get(key)
            if not item:
                self._stats.misses += 1
                return None
            ts, value = item
            if now - ts > self.ttl_s:
                # expired
                self._stats.misses += 1
                del self._data[key]
                return None
            # LRU touch
            self._data.move_to_end(key, last=True)
            self._stats.hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = (time.time(), value)
            self._data.move_to_end(key, last=True)
            self._evict_if_needed()

    def stats(self) -> dict:
        with self._lock:
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "size": len(self._data),
                "max_items": self.max_items,
                "ttl_s": self.ttl_s,
            }
