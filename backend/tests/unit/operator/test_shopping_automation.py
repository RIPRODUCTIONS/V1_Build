from __future__ import annotations

import types
import pytest

from app.operator.templates.shopping_automation import PersonalShoppingAssistant


@pytest.mark.asyncio
async def test_shopping_automation_aggregate_success(monkeypatch):
    # Enable operator web via settings stub
    import app.operator.templates.shopping_automation as mod

    monkeypatch.setattr(mod, "get_settings", lambda: types.SimpleNamespace(OPERATOR_WEB_REAL=True))

    auto = PersonalShoppingAssistant()

    # Stub platform searches
    async def _a(items):
        return items

    monkeypatch.setattr(auto, "_search_amazon", lambda q, m: _a([{"title": "A1", "price": "199", "url": "u"}]))
    monkeypatch.setattr(auto, "_search_ebay", lambda q, m: _a([{"title": "E1", "price": "150", "url": "u"}, {"title": "E2", "price": "89", "url": "u"}]))
    monkeypatch.setattr(auto, "_search_google_shopping", lambda q, m: _a([]))
    monkeypatch.setattr(auto, "_search_walmart", lambda q, m: _a([{"title": "W1", "price": "250", "url": "u"}]))

    res = await auto.execute({"product_query": "laptop", "max_results": 5})
    assert res["success"] is True
    # Counts
    assert res["amazon_count"] == 1
    assert res["ebay_count"] == 2
    assert res["google_count"] == 0
    assert res["walmart_count"] == 1
    assert res["total_results"] == 4
    # Price range should consider numeric coercion
    assert res["price_range"] == (89.0, 250.0)


@pytest.mark.asyncio
async def test_shopping_automation_disabled(monkeypatch):
    import app.operator.templates.shopping_automation as mod

    monkeypatch.setattr(mod, "get_settings", lambda: types.SimpleNamespace(OPERATOR_WEB_REAL=False))
    res = await PersonalShoppingAssistant().execute({"product_query": "phone"})
    assert res["success"] is False
    assert res["reason"] == "operator_web_real_disabled"


