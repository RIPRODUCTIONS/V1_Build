from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import get_settings
from app.operator.mvp_web_executor import MVPWebExecutor


class PersonalResearchAssistant:
    template_config = {
        "id": "research_assistant",
        "name": "Personal Research Assistant",
        "category": "research",
        "description": "Research topics, gather information, and create summaries",
    }

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        settings = get_settings()
        if not settings.OPERATOR_WEB_REAL:
            return {"success": False, "reason": "operator_web_real_disabled"}

        topic = parameters.get("topic") or "AI automation trends"

        scholar = await self._search_google_scholar(topic)
        reddit = await self._search_reddit_discussions(topic)
        # Stubs for future: news/github
        news: List[Dict[str, Any]] = []
        github: List[Dict[str, Any]] = []

        synthesis = {
            "summary": f"Found {len(scholar)} scholar results and {len(reddit)} reddit posts for '{topic}'.",
            "highlights": scholar[:3] + reddit[:3],
        }

        return {
            "success": True,
            "topic": topic,
            "sources_found": len(scholar) + len(reddit) + len(news) + len(github),
            "google_scholar": len(scholar),
            "reddit_discussions": len(reddit),
            "news_articles": len(news),
            "github_repos": len(github),
            "synthesis": synthesis,
            "research_data": (scholar + reddit)[:20],
        }

    async def _search_google_scholar(self, topic: str) -> List[Dict[str, Any]]:
        try:
            from playwright.async_api import async_playwright
        except Exception:
            return []

        executor = MVPWebExecutor()
        plan = {
            "steps": [
                {
                    "action": "navigate",
                    "target": "https://scholar.google.com",
                    "wait_for_content": True,
                    "expected_content": ["input", "q"],
                },
                {
                    "action": "search_and_extract",
                    "search_term": topic,
                    "search_selector": "input[name='q']",
                    "expected_results": [".gs_r", ".gs_rt"],
                    "extraction_rules": {
                        "title": ".gs_rt a",
                        "authors": ".gs_a",
                        "snippet": ".gs_rs",
                        "citations": ".gs_fl a",
                        "year": ".gs_a",
                    },
                },
            ]
        }
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            res = await executor.execute_plan_steps(page, plan)
            hit = next((r for r in (res.get("results") or []) if r.get("action") == "search_and_extract"), None)
            return (hit or {}).get("data", [])
        finally:
            await browser.close()
            await pw.stop()

    async def _search_reddit_discussions(self, topic: str) -> List[Dict[str, Any]]:
        try:
            from playwright.async_api import async_playwright
        except Exception:
            return []

        executor = MVPWebExecutor()
        plan = {
            "steps": [
                {
                    "action": "navigate",
                    "target": f"https://www.reddit.com/search/?q={topic.replace(' ', '+')}&type=sr%2Cuser",
                    "wait_for_content": True,
                    "expected_content": ["[data-testid='post']", ".Post"],
                },
                {
                    "action": "infinite_scroll_extract",
                    "target_count": 20,
                    "item_selector": "[data-testid='post']",
                    "extraction_rules": {
                        "title": "h3",
                        "subreddit": "[data-testid='subreddit-name']",
                        "comments": "[data-testid='comment-count']",
                        "url": "a[data-testid='post-title']",
                    },
                },
            ]
        }
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            res = await executor.execute_plan_steps(page, plan)
            hit = next((r for r in (res.get("results") or []) if r.get("action") == "infinite_scroll_extract"), None)
            return (hit or {}).get("data", [])
        finally:
            await browser.close()
            await pw.stop()


