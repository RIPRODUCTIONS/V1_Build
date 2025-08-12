from typing import Any

from app.automation.registry import skill


@skill('finance.ocr_and_categorize')
async def ocr_and_categorize(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, 'receipt_categorized': True}


@skill('finance.schedule_payment')
async def schedule_payment(context: dict[str, Any]) -> dict[str, Any]:
    return {**context, 'payment_scheduled': True}
