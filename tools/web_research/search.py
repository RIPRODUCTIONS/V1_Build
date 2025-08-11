from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

if TYPE_CHECKING:  # avoid import cost at runtime
    from .cache import TTLCache
    from .limiter import TokenBucket
from .metrics import (
    CACHE_HITS,
    CACHE_MISSES,
    SEARCH_ERRORS,
    SEARCH_LATENCY,
    SEARCH_REQUESTS,
)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""


def _canon_query(q: str) -> str:
    return " ".join(q.lower().split())


def _canon_url(u: str) -> str:
    parts = list(urlsplit(u))
    parts[4] = ""  # strip fragment
    return urlunsplit(parts)


class SearchAdapter:
    def __init__(
        self,
        cache: TTLCache | None = None,
        limiter: TokenBucket | None = None,
        fetch: Callable[[str], tuple[bytes, str, str]] | None = None,
    ) -> None:
        self.cache = cache
        self.limiter = limiter
        self.fetch = fetch or (lambda url: (b"", "text/plain", url))

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:  # pragma: no cover - proto
        raise NotImplementedError

    def search_and_extract(self, query: str, limit: int = 3):
        # Import locally but ruff prefers top-level; keeping here to minimize import costs
        from tools.web_research.normalize import normalize_text  # noqa: PLC0415

        adapter_name = self.__class__.__name__
        SEARCH_REQUESTS.labels(adapter_name).inc()
        key = f"q:{_canon_query(query)}:{limit}"
        if self.cache:
            cached = self.cache.get(key)
            if cached is not None:
                CACHE_HITS.labels(adapter_name).inc()
                return cached
            CACHE_MISSES.labels(adapter_name).inc()
        hits = self.search(query, limit=limit)
        results = []
        for h in hits:
            if self.limiter:
                self.limiter.wait()
            url_key = f"u:{_canon_url(h.url)}"
            raw_ct_final = None
            if self.cache:
                raw_ct_final = self.cache.get(url_key)
            if raw_ct_final is None:
                try:
                    with SEARCH_LATENCY.labels(adapter_name).time():
                        raw, ct, final = self.fetch(h.url)
                except Exception:
                    SEARCH_ERRORS.labels(adapter_name).inc()
                    raw, ct, final = b"", "text/plain", h.url
                raw_ct_final = (raw, ct, final)
                if self.cache:
                    self.cache.set(url_key, raw_ct_final)
            raw, ct, final = raw_ct_final
            results.append(normalize_text(final, ct, raw))
        if self.cache:
            self.cache.set(key, results)
        return results


class FakeSearchAdapter(SearchAdapter):
    def __init__(self, corpus: Iterable[SearchResult] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._corpus = list(
            corpus
            or [
                SearchResult("FastAPI Docs", "https://fastapi.tiangolo.com/"),
                SearchResult("Pydantic v2", "https://docs.pydantic.dev/latest/"),
            ]
        )

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        # naive return: top-N of corpus; stable for tests
        return self._corpus[:limit]


class FixtureSearchAdapter(SearchAdapter):
    def __init__(self, fixtures_dir: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dir = fixtures_dir
        self.index_path = os.path.join(self.dir, "search_index.json")
        if os.path.exists(self.index_path):
            with open(self.index_path, encoding="utf-8") as f:
                self.index = json.load(f)
        else:
            self.index = {}

    def _fixture_fetch(self, url: str) -> tuple[bytes, str, str]:
        from pathlib import Path  # noqa: PLC0415

        slug = _canon_url(url).replace("https://", "").replace("http://", "")
        slug = "".join([c if c.isalnum() else "_" for c in slug])
        for ext, ct in ((".html", "text/html"), (".txt", "text/plain")):
            p = Path(self.dir) / f"{slug}{ext}"
            if p.exists():
                return p.read_bytes(), ct, url
        return b"", "text/plain", url

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        urls = self.index.get(_canon_query(query), [])[:limit]
        return [SearchResult(title=u, url=u) for u in urls]
