from __future__ import annotations

from datetime import UTC, datetime

from app.security.deps import require_scopes
from app.security.scopes import ADMIN_TASKS
from fastapi import APIRouter, Depends

from .models import BuildResult, HealingResult, SystemHealth

router = APIRouter(prefix="/selfheal", tags=["selfheal"])


@router.get(
    "/health",
    response_model=list[SystemHealth],
)
async def get_system_health(user=Depends(require_scopes({ADMIN_TASKS}))) -> list[SystemHealth]:  # noqa: B008
    now = datetime.now(UTC)
    # Stub with a couple of components; extend with real checks later
    return [
        SystemHealth(
            component="api",
            health_score=0.95,
            issues=[],
            performance_metrics={"p95_latency_ms": 42.0},
            last_check=now,
        ),
        SystemHealth(
            component="worker",
            health_score=0.88,
            issues=["sporadic queue spikes"],
            performance_metrics={"tasks_pending": 3.0},
            last_check=now,
        ),
    ]


@router.post(
    "/heal",
    response_model=HealingResult,
)
async def trigger_healing(user=Depends(require_scopes({ADMIN_TASKS}))) -> HealingResult:  # noqa: B008
    # Stub OK response; to be replaced with actual orchestration
    return HealingResult(success=True, message="Healing initiated", strategy_applied="restart-component", attempts=1)


@router.post(
    "/rebuild",
    response_model=BuildResult,
)
async def trigger_self_build(user=Depends(require_scopes({ADMIN_TASKS}))) -> BuildResult:  # noqa: B008
    # Stub OK response
    return BuildResult(success=True, component="# generated component code ...", performance_improvements={"cpu": 0.12})


