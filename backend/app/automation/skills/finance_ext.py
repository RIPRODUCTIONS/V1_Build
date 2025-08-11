from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill("finance.portfolio_snapshot")
async def portfolio_snapshot(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "portfolio": {"positions": [{"sym": "AAPL", "qty": 10}]}}


@skill("finance.rebalance_suggest")
async def rebalance_suggest(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "rebalance": [{"sym": "AAPL", "action": "hold"}]}


@skill("finance.bill_detect")
async def bill_detect(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "bills": [{"vendor": "Utility", "amount": 120.55}]}


@skill("finance.bill_schedule")
async def bill_schedule(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "scheduled": True}


@skill("finance.receipt_ocr")
async def receipt_ocr(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "receipt_text": "TOTAL $12.34 MERCHANT ACME"}


@skill("finance.parse_amount")
async def parse_amount(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "amount": 12.34}


@skill("finance.categorize")
async def categorize(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "category": "Meals"}


@skill("finance.sync_accounting")
async def sync_accounting(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, "synced": True}
