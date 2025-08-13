from __future__ import annotations

from typing import Any, Dict, Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.operator.template_library import AutomationTemplateLibrary
from app.billing.pay_per_use import PayPerUseBilling
from app.models import AutomationTemplate, AutomationUsage


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
        usage_id = int(charge.get("usage_id"))
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


