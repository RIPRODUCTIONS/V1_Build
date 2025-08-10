from __future__ import annotations

from typing import Any

from app.automation.registry import skill


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
