from __future__ import annotations

import asyncio
import os
from contextlib import suppress
from pathlib import Path
from typing import Any, cast

try:
    from playwright.async_api import Browser, BrowserContext, Page, async_playwright  # type: ignore
except Exception:  # pragma: no cover
    async_playwright = None  # type: ignore
    Browser = BrowserContext = Page = object  # type: ignore


class BrowserOperator:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.sessions: dict[str, dict[str, Any]] = {}
        self.lock = asyncio.Lock()
        self.enabled = os.environ.get("ENABLE_BROWSER_OPERATOR", "0") == "1"

    async def _ensure_playwright(self) -> None:
        if not self.enabled:
            raise RuntimeError("browser_operator_disabled")
        if async_playwright is None:
            raise RuntimeError("playwright_not_installed")

    async def create_session(self, session_id: str, proxy: dict[str, str] | None = None) -> dict[str, Any]:
        await self._ensure_playwright()
        async with self.lock:
            if session_id in self.sessions:
                return {"session_id": session_id, "status": "exists"}
            profile_dir = self.data_dir / "profiles" / session_id
            profile_dir.mkdir(parents=True, exist_ok=True)
            pw = await async_playwright().start()  # type: ignore
            # Map simple proxy dict to Playwright ProxySettings if provided
            proxy_settings: Any = None
            if proxy and isinstance(proxy, dict):
                # Playwright ProxySettings expects keys like server, username, password
                server = proxy.get("server") or proxy.get("url") or proxy.get("http")
                if server and isinstance(server, str):
                    proxy_settings = {"server": server}
                    if isinstance(proxy.get("username"), str):
                        proxy_settings["username"] = proxy["username"]
                    if isinstance(proxy.get("password"), str):
                        proxy_settings["password"] = proxy["password"]
            # Cast to expected type for type checker
            browser = await pw.chromium.launch(headless=True, proxy=proxy_settings)  # type: ignore[arg-type]
            context = await browser.new_context(viewport={"width": 1280, "height": 800},
                                                storage_state=None,
                                                user_agent=None,
                                                record_video_dir=None,
                                                base_url=None)
            page = await context.new_page()
            self.sessions[session_id] = {"pw": pw, "browser": browser, "context": context, "page": page}
            return {"session_id": session_id, "status": "created"}

    async def list_sessions(self) -> list[str]:
        return list(self.sessions.keys())

    async def close_session(self, session_id: str) -> None:
        async with self.lock:
            s = self.sessions.pop(session_id, None)
        if s:
            with suppress(Exception):
                await s["context"].close()
            with suppress(Exception):
                await s["browser"].close()
            with suppress(Exception):
                await s["pw"].stop()

    def _get_page(self, session_id: str) -> Page:
        s = self.sessions.get(session_id)
        if not s:
            raise RuntimeError("session_not_found")
        return cast(Page, s["page"])

    async def navigate(self, session_id: str, url: str) -> dict[str, Any]:
        await self._ensure_playwright()
        page = self._get_page(session_id)
        resp = await page.goto(url, wait_until="domcontentloaded")
        status = getattr(resp, "status", None)
        return {"ok": True, "status": status if isinstance(status, int) else None, "url": page.url}

    async def search(self, session_id: str, engine: str, query: str) -> dict[str, Any]:
        await self._ensure_playwright()
        if engine.lower() == "google":
            url = f"https://www.google.com/search?q={query}"
        else:
            url = f"https://www.bing.com/search?q={query}"
        return await self.navigate(session_id, url)

    async def screenshot(self, session_id: str, out_dir: Path) -> dict[str, Any]:
        page = self._get_page(session_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        file = out_dir / f"shot-{session_id}.png"
        await page.screenshot(path=str(file), full_page=True)
        return {"path": str(file)}





