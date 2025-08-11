from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill("shopping.price_track")
async def price_track(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "prices": [{"item": "Widget", "price": 19.99}]}


@skill("shopping.cart_optimize")
async def cart_optimize(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "cart": {"savings": 5.0}}


@skill("shopping.receipt_categorize")
async def receipt_categorize(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "receipt": {"category": "groceries"}}
