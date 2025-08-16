from __future__ import annotations

from typing import Any


class DemoAutomations:
    async def contact_form_automation(self, website_url: str, contact_details: dict[str, Any]) -> dict[str, Any]:
        return {"url": website_url, "submitted": False, "status": "disabled"}

    async def data_extraction_automation(self, product_url: str) -> dict[str, Any]:
        return {"url": product_url, "data": {}, "status": "disabled"}

    async def account_signup_automation(self, signup_url: str, user_details: dict[str, Any]) -> dict[str, Any]:
        return {"url": signup_url, "account_created": False, "status": "disabled"}


