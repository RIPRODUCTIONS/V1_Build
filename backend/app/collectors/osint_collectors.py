from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import get_settings


def safe_playwright_available() -> bool:
    try:
        import playwright  # type: ignore
        return True
    except Exception:
        return False


class BaseCollector:
    def __init__(self, platform: str) -> None:
        self.platform = platform

    async def collect(self, query: str) -> List[Dict[str, Any]]:
        settings = get_settings()
        if not (settings.OPERATOR_WEB_REAL and safe_playwright_available()):
            return []
        # Default no-op; concrete collectors can override
        return []


class LinkedInCollector(BaseCollector):
    def __init__(self) -> None:
        super().__init__("linkedin")

    async def collect(self, query: str) -> List[Dict[str, Any]]:  # pragma: no cover - network
        settings = get_settings()
        if not (settings.OPERATOR_WEB_REAL and safe_playwright_available()):
            return []
        try:
            from playwright.async_api import async_playwright  # type: ignore
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()
                url = f"https://www.linkedin.com/search/results/people/?keywords={query.replace(' ', '%20')}"
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                anchors = await page.query_selector_all("a.app-aware-link")
                out: List[Dict[str, Any]] = []
                for a in anchors[:20]:
                    href = await a.get_attribute("href")
                    text = (await a.text_content()) or ""
                    if href and text:
                        out.append({"url": href, "text": text.strip()})
                await browser.close()
                return out
        except Exception:
            return []


class TwitterCollector(BaseCollector):
    def __init__(self) -> None:
        super().__init__("twitter")

    async def collect(self, query: str) -> List[Dict[str, Any]]:  # pragma: no cover - network
        settings = get_settings()
        if not (settings.OPERATOR_WEB_REAL and safe_playwright_available()):
            return []
        try:
            from playwright.async_api import async_playwright  # type: ignore
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()
                url = f"https://twitter.com/search?q={query.replace(' ', '%20')}"
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                tweets = await page.query_selector_all("article")
                out: List[Dict[str, Any]] = []
                for t in tweets[:20]:
                    content = (await t.text_content()) or ""
                    if content.strip():
                        out.append({"text": content.strip()[:280]})
                await browser.close()
                return out
        except Exception:
            return []


class RedditCollector(BaseCollector):
    def __init__(self) -> None:
        super().__init__("reddit")

    async def collect(self, query: str) -> List[Dict[str, Any]]:  # pragma: no cover - network
        settings = get_settings()
        if not (settings.OPERATOR_WEB_REAL and safe_playwright_available()):
            return []
        try:
            from playwright.async_api import async_playwright  # type: ignore
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()
                url = f"https://www.reddit.com/search/?q={query.replace(' ', '+')}"
                await page.goto(url, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                posts = await page.query_selector_all("[data-testid='post-container']")
                out: List[Dict[str, Any]] = []
                for p in posts[:20]:
                    content = (await p.text_content()) or ""
                    if content.strip():
                        out.append({"text": content.strip()[:280]})
                await browser.close()
                return out
        except Exception:
            return []


def get_collectors() -> List[BaseCollector]:
    return [LinkedInCollector(), TwitterCollector(), RedditCollector()]


