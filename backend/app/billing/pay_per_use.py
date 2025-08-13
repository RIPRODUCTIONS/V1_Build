from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models import UserCredits, AutomationUsage


class PayPerUseBilling:
    """Simple pay-per-use credits system. Stripe integration can be added later."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_wallet(self, user_id: int) -> UserCredits:
        wallet = self.db.get(UserCredits, user_id)
        if not wallet:
            wallet = UserCredits(user_id=user_id, credits_balance=0.0, total_spent=0.0)
            self.db.add(wallet)
            self.db.commit()
            self.db.refresh(wallet)
        return wallet

    def create_prepaid_credits(self, user_id: int, amount_usd: float) -> Dict[str, Any]:
        amount = max(0.0, float(amount_usd))
        wallet = self.get_or_create_wallet(user_id)
        # Simple bonus tiers
        bonus = 0.0
        if amount >= 500:
            bonus = amount * 0.30
        elif amount >= 100:
            bonus = amount * 0.20
        elif amount >= 20:
            bonus = 0.0  # no bonus for small packs by default
        wallet.credits_balance += amount + bonus
        wallet.last_purchase = datetime.utcnow()
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return {
            "user_id": user_id,
            "balance_usd": round(wallet.credits_balance, 2),
            "bonus_usd": round(bonus, 2),
        }

    def charge_for_automation(self, user_id: int, template_id: str, cost_usd: float) -> Dict[str, Any]:
        cost = max(0.0, float(cost_usd))
        wallet = self.get_or_create_wallet(user_id)
        if wallet.credits_balance < cost:
            return {"ok": False, "error": "insufficient_credits", "balance_usd": round(wallet.credits_balance, 2)}
        wallet.credits_balance -= cost
        wallet.total_spent += cost
        usage = AutomationUsage(user_id=user_id, template_id=template_id, cost_usd=cost, success=True)
        self.db.add(wallet)
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(wallet)
        self.db.refresh(usage)
        return {
            "ok": True,
            "balance_usd": round(wallet.credits_balance, 2),
            "usage_id": usage.id,
        }


