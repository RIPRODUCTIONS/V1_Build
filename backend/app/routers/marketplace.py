from __future__ import annotations

from typing import Any, Dict, Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.operator.template_library import AutomationTemplateLibrary
from app.billing.pay_per_use import PayPerUseBilling
from app.models import AutomationTemplate, AutomationUsage, ProcessedCheckoutSession, UserCredits


router = APIRouter(prefix="/marketplace", tags=["marketplace"])


def get_current_user_id() -> int:
    # Minimal stub for now; integrate real auth later
    return 1


@router.get("/templates")
async def list_marketplace_templates(db: Annotated[Session, Depends(get_db)]) -> Dict[str, Any]:
    lib = AutomationTemplateLibrary()
    items = await lib.list_templates_by_category(None)
    # Ensure DB-backed price if available
    db_prices: dict[str, float | None] = {}
    rows = db.query(AutomationTemplate).all()
    for r in rows:
        db_prices[r.id] = r.price_per_run_usd
    for it in items:
        if it.get("id") in db_prices and db_prices[it["id"]] is not None:
            it["price_per_run_usd"] = db_prices[it["id"]]
    return {"templates": items}


@router.post("/buy_credits")
async def buy_credits(amount_usd: float, db: Annotated[Session, Depends(get_db)]) -> Dict[str, Any]:
    user_id = get_current_user_id()
    billing = PayPerUseBilling(db)
    return billing.create_prepaid_credits(user_id, amount_usd)


@router.post("/buy_credits/checkout")
async def buy_credits_checkout(amount_usd: float, db: Annotated[Session, Depends(get_db)]) -> Dict[str, Any]:
    """Create a Stripe Checkout Session for credits purchase when STRIPE_SECRET_KEY is configured.

    The frontend should redirect to the returned url. On success (webhook or client return),
    call /marketplace/buy_credits/confirm with the session_id to finalize crediting.
    """
    from app.core.config import get_settings
    s = get_settings()
    if not s.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=400, detail={"error": "stripe_not_configured"})

    import stripe  # type: ignore

    stripe.api_key = s.STRIPE_SECRET_KEY
    try:
        amount_cents = int(round(max(0.0, float(amount_usd)) * 100))
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "invalid_amount"})
    if amount_cents <= 0:
        raise HTTPException(status_code=400, detail={"error": "invalid_amount"})
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Automation Credits"},
                "unit_amount": amount_cents,
            },
            "quantity": 1,
        }],
        success_url="http://localhost:3000/marketplace?success=1&session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:3000/marketplace?canceled=1",
    )
    return {"id": session["id"], "url": session["url"]}


@router.post("/buy_credits/confirm")
async def buy_credits_confirm(session_id: str, db: Annotated[Session, Depends(get_db)]) -> Dict[str, Any]:
    """Confirm a Stripe Checkout session and credit the user, idempotently."""
    from app.core.config import get_settings
    s = get_settings()
    if not s.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=400, detail={"error": "stripe_not_configured"})

    # Idempotency: avoid double-credit for same session
    if db.get(ProcessedCheckoutSession, session_id):
        wallet = db.get(UserCredits, get_current_user_id())
        return {"status": "ok", "already_confirmed": True, "balance_usd": round((wallet and wallet.credits_balance) or 0.0, 2)}

    import stripe  # type: ignore

    stripe.api_key = s.STRIPE_SECRET_KEY
    sess = stripe.checkout.Session.retrieve(session_id)
    if sess and sess.get("payment_status") == "paid":
        try:
            amount_paid = float(sess.get("amount_total", 0) or 0) / 100.0
        except Exception:
            amount_paid = 0.0
        user_id = get_current_user_id()
        # Apply credits and record processed session
        billing = PayPerUseBilling(db)
        info = billing.create_prepaid_credits(user_id, amount_paid)
        db.add(ProcessedCheckoutSession(session_id=session_id, credited_amount_usd=amount_paid))
        db.commit()
        return {"status": "ok", "balance_usd": info.get("balance_usd", 0.0)}
    raise HTTPException(status_code=400, detail={"error": "payment_not_completed"})


@router.post("/run/{template_id}")
async def run_template(template_id: str, parameters: Dict[str, Any], db: Annotated[Session, Depends(get_db)]) -> Dict[str, Any]:
    # Look up template to determine price
    lib = AutomationTemplateLibrary()
    try:
        t = await lib.get_template(template_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="template not found")
    # Prefer DB price if present
    row = db.query(AutomationTemplate).filter(AutomationTemplate.id == template_id).first()
    unit_price = None
    if row and row.price_per_run_usd is not None:
        unit_price = float(row.price_per_run_usd)
    else:
        unit_price = float(t.get("price_per_run_usd") or 0.0)

    # Queue the work using existing template deployment logic
    from app.routers.template_library import _queue_for_template  # local import to avoid circular deps at import time

    enqueue_result = await _queue_for_template(template_id, parameters)
    if (enqueue_result or {}).get("status") != "queued":
        raise HTTPException(status_code=400, detail={"error": "template_not_queueable", "result": enqueue_result})
    task_ids = (enqueue_result or {}).get("task_ids") or []
    task_count = len(task_ids) if isinstance(task_ids, list) and task_ids else 1
    total_price = round(unit_price * task_count, 2)

    # Charge after successful enqueue
    user_id = get_current_user_id()
    billing = PayPerUseBilling(db)
    charge = billing.charge_for_automation(user_id, template_id, total_price)
    if not charge.get("ok"):
        raise HTTPException(status_code=402, detail=charge)

    # Attach a simple receipt summary to the usage record
    try:
        raw_usage_id = charge.get("usage_id")
        usage_id = int(raw_usage_id) if raw_usage_id is not None else -1
        rec = db.get(AutomationUsage, usage_id)
        if rec:
            import json as _json
            rec.results_summary_json = _json.dumps({
                "task_ids": task_ids,
                "task_count": task_count,
                "unit_price_usd": unit_price,
                "total_price_usd": total_price,
            })
            db.add(rec)
            db.commit()
    except Exception:
        pass

    return {
        "status": "queued",
        "template_id": template_id,
        "tasks": enqueue_result,
        "unit_price_usd": unit_price,
        "task_count": task_count,
        "total_price_usd": total_price,
        "billing": charge,
    }


@router.get("/usage")
async def get_usage(db: Annotated[Session, Depends(get_db)], limit: int = 20) -> Dict[str, Any]:
    user_id = get_current_user_id()
    rows = (
        db.query(AutomationUsage)
        .filter(AutomationUsage.user_id == user_id)
        .order_by(AutomationUsage.executed_at.desc())
        .limit(max(1, min(200, int(limit))))
        .all()
    )
    items: list[dict] = []
    for r in rows:
        try:
            summary = r.results_summary_json and __import__("json").loads(r.results_summary_json) or None
        except Exception:
            summary = None
        items.append(
            {
                "id": r.id,
                "template_id": r.template_id,
                "cost_usd": r.cost_usd,
                "executed_at": r.executed_at.isoformat(),
                "success": bool(r.success),
                "summary": summary,
            }
        )
    return {"items": items}

@router.get("/credits")
async def get_credits(db: Annotated[Session, Depends(get_db)]) -> Dict[str, Any]:
    user_id = get_current_user_id()
    billing = PayPerUseBilling(db)
    wallet = billing.get_or_create_wallet(user_id)
    return {
        "user_id": user_id,
        "balance_usd": round(wallet.credits_balance, 2),
        "total_spent_usd": round(wallet.total_spent, 2),
        "last_purchase": wallet.last_purchase.isoformat() if wallet.last_purchase else None,
    }


