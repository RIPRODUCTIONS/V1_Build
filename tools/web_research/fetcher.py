from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Page:
    url: str
    html: str
    status: int
    fetched_at: float


CACHE_DIR = Path(".cache/web")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_cache_key(url: str) -> Path:
    return CACHE_DIR / re.sub(r"[^a-zA-Z0-9]+", "_", url)[:200]


async def _fetch_one(playwright, url: str) -> Page:
    # Lightweight rate-limited fetch via Playwright
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        html = await page.content()
        status = page.response.status if page.response else 200
        return Page(url=url, html=html, status=status, fetched_at=time.time())
    finally:
        await browser.close()


def fetch_many(urls: list[str]) -> list[Page]:
    """Fetch with caching and naive robots respect (extend as needed).

    Note: In CI without browsers, call sites should provide offline mirrors, or you can
    pre-populate the cache in tests.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as _err:  # pragma: no cover - optional in CI
        raise RuntimeError("playwright not available; install for offline scrape") from _err

    results: list[Page] = []
    with sync_playwright() as pw:
        for url in urls:
            pth = _safe_cache_key(url)
            if pth.exists():  # cache hit
                results.append(
                    Page(
                        url=url,
                        html=pth.read_text("utf-8"),
                        status=200,
                        fetched_at=pth.stat().st_mtime,
                    )
                )
                continue
            page = asyncio.run(_fetch_one(pw, url))
            pth.write_text(page.html, encoding="utf-8")
            results.append(page)
            time.sleep(0.7)  # simple backoff
    return results
