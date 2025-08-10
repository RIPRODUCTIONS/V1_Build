from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import urlsplit, urlunsplit


@dataclass
class TextBlock:
    id: str
    text: str
    offset: int
    meta: dict


@dataclass
class ExtractResult:
    title: str
    language: str | None
    blocks: list[TextBlock]
    canonical_url: str
    word_count: int


def _normalize_url(url: str) -> str:
    parts = list(urlsplit(url))
    parts[4] = ""  # strip fragment
    return urlunsplit(parts)


def _split_paragraphs(text: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    return paras


def _dedup_blocks(blocks: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for b in blocks:
        key = re.sub(r"\s+", " ", b.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out


def normalize_text(url: str, content_type: str, raw: bytes) -> ExtractResult:
    ct = (content_type or "").lower()
    canon = _normalize_url(url)
    title = ""
    lang: str | None = None
    blocks: list[TextBlock] = []
    text: str
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = raw.decode(errors="replace")
    if "text/html" in ct or "html" in ct:
        # Heuristic HTML extraction without heavy deps
        # Remove scripts/styles
        sanitized = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
        sanitized = re.sub(r"<style[\s\S]*?</style>", " ", sanitized, flags=re.I)
        # Capture title
        m = re.search(r"<title>(.*?)</title>", sanitized, flags=re.I | re.S)
        if m:
            title = unescape(re.sub(r"\s+", " ", m.group(1)).strip())
        # Insert paragraph separators for common block tags
        block_tag_pattern = r"</?(p|div|li|h1|h2|h3|br|section|article|ul|ol)\b[^>]*>"
        with_separators = re.sub(block_tag_pattern, "\n\n", sanitized, flags=re.I)
        # Strip remaining tags
        body = re.sub(r"<[^>]+>", " ", with_separators)
        body = unescape(body)
        # Normalize whitespace but preserve paragraph separators
        body = re.sub(r"[ \t]+", " ", body)
        body = re.sub(r"\n{3,}", "\n\n", body)
        body = body.strip()
        paras = _split_paragraphs(body)
    else:
        paras = _split_paragraphs(text)
    paras = [p for p in paras if p]
    paras = _dedup_blocks(paras)
    word_count = 0
    for idx, p in enumerate(paras[:200]):  # cap blocks
        word_count += len(p.split())
        blocks.append(
            TextBlock(id=f"p{idx+1}", text=p[:2000], offset=idx, meta={"source_url": canon})
        )
    return ExtractResult(
        title=title, language=lang, blocks=blocks, canonical_url=canon, word_count=word_count
    )
