import asyncio
from typing import Any, Dict, List, Optional

try:  # optional runtime dep; guarded by feature flag
    from playwright.async_api import (
        async_playwright,
        Browser,
        Page,
        BrowserContext,
    )
except Exception:  # pragma: no cover - keep import optional for CI
    Browser = Page = BrowserContext = object  # type: ignore
    async_playwright = None  # type: ignore


class AutonomousWebDriver:
    def __init__(self) -> None:
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize_browser(self, headless: bool = True, viewport: Dict | None = None) -> Optional[Browser]:
        """Initialize Playwright browser with safe defaults. No-op if Playwright unavailable."""
        if async_playwright is None:
            return None
        viewport = viewport or {"width": 1280, "height": 800}
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=headless, args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ])
        context = await browser.new_context(viewport=viewport)
        page = await context.new_page()
        self.browser, self.context, self.page = browser, context, page
        return browser

    async def create_isolated_context(self, cookies: List[Dict] | None = None) -> Optional[BrowserContext]:
        """Create isolated browser context for each task. No-op if Playwright unavailable."""
        if self.browser is None or async_playwright is None:
            return None
        ctx = await self.browser.new_context()
        if cookies:
            await ctx.add_cookies(cookies)  # type: ignore[arg-type]
        self.context = ctx
        self.page = await ctx.new_page()
        return ctx

    async def close(self) -> None:
        try:
            if self.context is not None:
                await self.context.close()  # type: ignore[func-returns-value]
        except Exception:
            pass
        try:
            if self.browser is not None:
                await self.browser.close()  # type: ignore[func-returns-value]
        except Exception:
            pass


