from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import get_settings
from app.operator.mvp_web_executor import MVPWebExecutor


class PersonalShoppingAssistant:
    template_config = {
        "id": "shopping_assistant",
        "name": "Personal Shopping Assistant",
        "category": "shopping",
        "description": "Find best deals, track prices, and manage purchases",
    }

    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        settings = get_settings()
        if not settings.OPERATOR_WEB_REAL:
            return {"success": False, "reason": "operator_web_real_disabled"}

        query = parameters.get("product_query") or "laptop"
        max_results = int(parameters.get("max_results", 20))

        amazon = await self._search_amazon(query, max_results)
        ebay = await self._search_ebay(query, max_results)
        google = await self._search_google_shopping(query, max_results)
        walmart = await self._search_walmart(query, max_results)

        all_results = amazon + ebay + google + walmart
        price_values = []
        for p in all_results:
            try:
                val = float(str(p.get("price", "").replace(",", "").strip()))
                price_values.append(val)
            except Exception:
                pass
        analysis = {
            "price_range": (min(price_values), max(price_values)) if price_values else None,
            "best_deals": all_results[: min(len(all_results), 5)],
            "recommendations": ["Consider top-rated items with mid-range prices"],
        }
        return {
            "success": True,
            "product_query": query,
            "total_results": len(all_results),
            "amazon_count": len(amazon),
            "ebay_count": len(ebay),
            "google_count": len(google),
            "walmart_count": len(walmart),
            "best_deals": analysis.get("best_deals"),
            "price_range": analysis.get("price_range"),
            "recommendations": analysis.get("recommendations"),
            "all_results": all_results,
        }

    async def _search_amazon(self, product_query: str, max_results: int) -> List[Dict[str, Any]]:
        from playwright.async_api import async_playwright

        executor = MVPWebExecutor()
        plan = {
            "steps": [
                {
                    "action": "navigate",
                    "target": "https://www.amazon.com",
                    "wait_for_content": True,
                    "expected_content": ["#twotabsearchtextbox"],
                },
                {
                    "action": "search_and_extract",
                    "search_term": product_query,
                    "search_selector": "#twotabsearchtextbox",
                    "expected_results": ["[data-component-type='s-search-result']"],
                    "extraction_rules": {
                        "title": "h2 a span",
                        "price": ".a-price-whole",
                        "rating": ".a-icon-alt",
                        "url": "h2 a",
                    },
                },
                {
                    "action": "infinite_scroll_extract",
                    "target_count": max_results,
                    "item_selector": "[data-component-type='s-search-result']",
                    "extraction_rules": {
                        "title": "h2 a span",
                        "price": ".a-price-whole",
                        "rating": ".a-icon-alt",
                        "reviews": ".a-size-base",
                        "prime": ".a-icon-prime",
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
            products = (hit or {}).get("data", [])
            for p in products:
                p["platform"] = "Amazon"
                p["platform_url"] = "amazon.com"
            return products
        finally:
            await browser.close()
            await pw.stop()

    async def _search_ebay(self, product_query: str, max_results: int) -> List[Dict[str, Any]]:
        from playwright.async_api import async_playwright

        executor = MVPWebExecutor()
        plan = {
            "steps": [
                {
                    "action": "navigate",
                    "target": "https://www.ebay.com",
                    "wait_for_content": True,
                    "expected_content": ["#gh-ac"],
                },
                {
                    "action": "search_and_extract",
                    "search_term": product_query,
                    "search_selector": "#gh-ac",
                    "expected_results": [".s-item"],
                    "extraction_rules": {
                        "title": "h3.s-item__title",
                        "price": ".s-item__price",
                        "rating": ".x-star-rating span",
                        "url": "a.s-item__link",
                    },
                },
                {
                    "action": "infinite_scroll_extract",
                    "target_count": max_results,
                    "item_selector": ".s-item",
                    "extraction_rules": {
                        "title": "h3.s-item__title",
                        "price": ".s-item__price",
                        "rating": ".x-star-rating span",
                        "shipping": ".s-item__shipping",
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
            items = (hit or {}).get("data", [])
            for it in items:
                it["platform"] = "eBay"
                it["platform_url"] = "ebay.com"
            return items
        finally:
            await browser.close()
            await pw.stop()

    async def _search_google_shopping(self, product_query: str, max_results: int) -> List[Dict[str, Any]]:
        from playwright.async_api import async_playwright

        executor = MVPWebExecutor()
        url = f"https://www.google.com/search?tbm=shop&q={product_query.replace(' ', '+')}"
        plan = {
            "steps": [
                {
                    "action": "navigate",
                    "target": url,
                    "wait_for_content": True,
                    "expected_content": [".sh-dgr__content", ".sh-pr__product-results"],
                },
                {
                    "action": "infinite_scroll_extract",
                    "target_count": max_results,
                    "item_selector": ".sh-dgr__content",
                    "extraction_rules": {
                        "title": ".tAxDx",
                        "price": ".a8Pemb",
                        "url": "a.shntl",
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
            items = (hit or {}).get("data", [])
            for it in items:
                it["platform"] = "Google Shopping"
                it["platform_url"] = "google.com/shopping"
            return items
        finally:
            await browser.close()
            await pw.stop()

    async def _search_walmart(self, product_query: str, max_results: int) -> List[Dict[str, Any]]:
        from playwright.async_api import async_playwright

        executor = MVPWebExecutor()
        url = f"https://www.walmart.com/search?q={product_query.replace(' ', '+')}"
        plan = {
            "steps": [
                {
                    "action": "navigate",
                    "target": url,
                    "wait_for_content": True,
                    "expected_content": ["input[type='search']"],
                },
                {
                    "action": "infinite_scroll_extract",
                    "target_count": max_results,
                    "item_selector": "[data-automation-id='search-product-result']",
                    "extraction_rules": {
                        "title": "a span",
                        "price": "span[class*='price']",
                        "rating": "span[aria-label*='out of']",
                        "url": "a",
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
            items = (hit or {}).get("data", [])
            for it in items:
                it["platform"] = "Walmart"
                it["platform_url"] = "walmart.com"
            return items
        finally:
            await browser.close()
            await pw.stop()


