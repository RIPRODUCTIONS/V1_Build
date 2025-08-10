from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Citation:
    id: str
    title: str
    url: str
    accessed_at: float
    key_points: list[str] = field(default_factory=list)


class CitationLedger:
    def __init__(self) -> None:
        self._items: list[Citation] = []

    def add(self, title: str, url: str, accessed_at: float, key_points: list[str]) -> str:
        cid = f"CIT-{len(self._items) + 1}"
        self._items.append(
            Citation(id=cid, title=title, url=url, accessed_at=accessed_at, key_points=key_points)
        )
        return cid

    def as_markdown(self) -> str:
        lines = []
        for c in self._items:
            lines.append(f"- [{c.id}] {c.title} — {c.url}")
        return "\n".join(lines)
