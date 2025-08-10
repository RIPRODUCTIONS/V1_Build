from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""


class SearchAdapter:
    def search(self, query: str, limit: int = 5) -> list[SearchResult]:  # pragma: no cover - proto
        raise NotImplementedError


class FakeSearchAdapter(SearchAdapter):
    def __init__(self, corpus: Iterable[SearchResult] | None = None) -> None:
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
