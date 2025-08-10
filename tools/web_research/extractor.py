from __future__ import annotations

from bs4 import BeautifulSoup


def extract_canonical_text(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "").strip() if soup.title else ""
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return {"title": title, "text": text[:150000]}
