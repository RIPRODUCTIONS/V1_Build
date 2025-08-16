from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.billing.pay_per_use import PayPerUseBilling
from app.models import UserCredits
from sqlalchemy.orm import Session


class NewUserOnboarding:
    """Convert visitors to paying customers with smooth onboarding.

    Grants $5 free credits on first call and returns a simple checklist
    with recommended templates.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def welcome_new_user(self, user_id: int, signup_source: str | None = None) -> dict[str, Any]:
        # Grant $5 credits if wallet missing or balance is zero and not previously credited
        wallet = self.db.get(UserCredits, user_id)
        if not wallet or (wallet and wallet.credits_balance <= 0.0 and wallet.total_spent <= 0.0):
            billing = PayPerUseBilling(self.db)
            billing.create_prepaid_credits(user_id, 5.0)

        # Basic recommendations (could use usage analytics later)
        recommendations = [
            {"id": "linkedin_lead_extractor", "reason": "Fast path to leads"},
            {"id": "ecommerce_price_spy", "reason": "Clear price ROI"},
            {"id": "contact_form_lead_generator", "reason": "Simple first run"},
        ]
        checklist = [
            {"step": 1, "title": "Buy or claim free credits", "completed": True},
            {"step": 2, "title": "Run your first template", "completed": False},
            {"step": 3, "title": "View receipts & ROI", "completed": False},
        ]
        return {
            "granted_credits": 5.0,
            "recommendations": recommendations,
            "checklist": checklist,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "signup_source": signup_source,
        }

    def status(self, user_id: int) -> dict[str, Any]:
        wallet = self.db.get(UserCredits, user_id)
        balance = (wallet and wallet.credits_balance) or 0.0
        checklist = [
            {"step": 1, "title": "Credits available", "completed": balance > 0.0},
            {"step": 2, "title": "Run your first template", "completed": False},
            {"step": 3, "title": "View receipts & ROI", "completed": False},
        ]
        return {"balance_usd": round(balance, 2), "checklist": checklist}


