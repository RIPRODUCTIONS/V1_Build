from __future__ import annotations

from typing import Annotated, Any

from app.db import get_db
from app.onboarding.new_user_flow import NewUserOnboarding
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


def get_current_user_id() -> int:
    # Minimal stub for now; integrate real auth later
    return 1


@router.post("/start")
def start_onboarding(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    user_id = get_current_user_id()
    flow = NewUserOnboarding(db)
    result = flow.welcome_new_user(user_id)
    return {
        "free_credits_granted": 5.00,
        "recommended_templates": result["recommendations"],
        "onboarding_steps": result["checklist"],
        "tutorial_enabled": True,
    }


@router.get("/status")
def get_onboarding_status(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    user_id = get_current_user_id()
    flow = NewUserOnboarding(db)
    return flow.status(user_id)


