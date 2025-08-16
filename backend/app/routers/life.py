from __future__ import annotations

import uuid
from typing import Any

from app.automation.idempotency import claim_or_get, store_result
from app.automation.orchestrator import run_dag
from app.automation.state import set_status
from app.core.config import get_settings
from app.security.jwt_hs256 import HS256JWT
from fastapi import APIRouter, Depends, Header, HTTPException
from prometheus_client import Counter, Histogram
from pydantic import BaseModel

# Life-specific metrics
LIFE_REQUESTS_TOTAL = Counter('life_requests_total', 'Total life automation requests', ['endpoint', 'status'])
LIFE_REQUEST_LATENCY = Histogram('life_request_latency_seconds', 'Life request latency in seconds', ['endpoint'])

router = APIRouter(prefix="/life", tags=["life-automation"])


import time


async def verify_jwt_token(authorization: str | None = Header(None)) -> dict:
    """Verify JWT token and return claims."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization[7:]  # Remove "Bearer " prefix

    try:
        settings = get_settings()
        jwt_handler = HS256JWT(secret=settings.jwt_secret)
        claims = jwt_handler.verify(token)

        # Check if token has required subject claim
        if "sub" not in claims:
            raise HTTPException(status_code=403, detail="Token missing subject claim")

        return claims

    except HTTPException:
        # Re-raise HTTP exceptions (like 403) as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}") from e


async def track_life_metrics(endpoint: str, status: int, duration: float):
    """Track life-specific metrics."""
    LIFE_REQUESTS_TOTAL.labels(endpoint=endpoint, status=status).inc()
    LIFE_REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)


class SimpleReq(BaseModel):
    payload: dict[str, Any] | None = None
    idempotency_key: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "payload": {
                    "user_id": "user-123",
                    "preferences": {
                        "category": "finance",
                        "timeframe": "daily"
                    }
                },
                "idempotency_key": "unique-request-id-123"
            }
        }
    }


class EnqueuedResponse(BaseModel):
    run_id: str
    status: str


async def _inline(
    intent: str, payload: dict[str, Any] | None, idem_key: str | None
) -> EnqueuedResponse:
    p = payload or {}
    key, cached = await claim_or_get(intent, p, idem_key)
    if cached:
        return EnqueuedResponse(**cached)
    run_id = str(uuid.uuid4())
    await set_status(run_id, "queued", {"intent": intent})
    # Directly enqueue orchestration; steps are resolved by orchestrator from registered DAGs
    await run_dag(run_id, [], dict(p))
    resp = {"run_id": run_id, "status": "queued"}
    await store_result(key, resp)
    return EnqueuedResponse(**resp)


@router.post("/health/wellness", response_model=EnqueuedResponse)
async def wellness(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("health.wellness_daily", {}, None)


@router.post("/nutrition/plan", response_model=EnqueuedResponse)
async def nutrition(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("nutrition.plan", {}, None)


@router.post("/home/evening", response_model=EnqueuedResponse)
async def home(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("home.evening_scene", {}, None)


@router.post("/transport/commute", response_model=EnqueuedResponse)
async def transport(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("transport.commute", {}, None)


@router.post("/learning/upskill", response_model=EnqueuedResponse)
async def learning(_: SimpleReq) -> EnqueuedResponse:
    return await _inline("learning.upskill", {}, None)


@router.post("/finance/investments", response_model=EnqueuedResponse, openapi_extra={
    "requestBody": {
        "content": {
            "application/json": {
                "examples": {
                    "investment_analysis": {
                        "summary": "Daily Investment Analysis",
                        "description": "Trigger daily investment portfolio analysis and optimization",
                        "value": {
                            "payload": {
                                "user_id": "user-123",
                                "preferences": {
                                    "category": "finance",
                                    "timeframe": "daily"
                                }
                            },
                            "idempotency_key": "daily-investment-123"
                        }
                    }
                }
            }
        }
    }
})
async def finance_investments(
    _: SimpleReq,
    claims: dict = Depends(verify_jwt_token)  # noqa: B008
) -> EnqueuedResponse:
    """
    Trigger daily investment analysis and optimization.

    This endpoint initiates automated investment portfolio analysis,
    including risk assessment, rebalancing recommendations, and
    market opportunity identification.
    """
    start_time = time.time()
    try:
        result = await _inline("finance.investments_daily", {}, None)
        duration = time.time() - start_time
        await track_life_metrics("finance_investments", 200, duration)
        return result
    except Exception:
        duration = time.time() - start_time
        await track_life_metrics("finance_investments", 500, duration)
        raise


@router.post("/finance/bills", response_model=EnqueuedResponse, openapi_extra={
    "requestBody": {
        "content": {
            "application/json": {
                "examples": {
                    "bills_analysis": {
                        "summary": "Monthly Bills Analysis",
                        "description": "Analyze monthly bills and identify optimization opportunities",
                        "value": {
                            "payload": {
                                "user_id": "user-123",
                                "preferences": {
                                    "category": "bills",
                                    "timeframe": "monthly"
                                }
                            },
                            "idempotency_key": "monthly-bills-123"
                        }
                    }
                }
            }
        }
    }
})
async def finance_bills(_: SimpleReq, claims: dict = Depends(verify_jwt_token)) -> EnqueuedResponse:  # noqa: B008
    return await _inline("finance.bills_monthly", {}, None)


@router.post("/security/sweep", response_model=EnqueuedResponse, openapi_extra={
    "requestBody": {
        "content": {
            "application/json": {
                "examples": {
                    "security_sweep": {
                        "summary": "Weekly Security Sweep",
                        "description": "Perform comprehensive security sweep and threat assessment",
                        "value": {
                            "payload": {
                                "user_id": "user-123",
                                "preferences": {
                                    "category": "security",
                                    "timeframe": "weekly"
                                }
                            },
                            "idempotency_key": "weekly-security-123"
                        }
                    }
                }
            }
        }
    }
})
async def security_sweep(_: SimpleReq, claims: dict = Depends(verify_jwt_token)) -> EnqueuedResponse:  # noqa: B008
    """
    Perform comprehensive security sweep and threat assessment.

    This endpoint initiates automated security analysis including
    vulnerability scanning, threat detection, and security posture
    evaluation across all connected systems and networks.
    """
    return await _inline("security.weekly_sweep", {}, None)


@router.post("/travel/plan", response_model=EnqueuedResponse, openapi_extra={
    "requestBody": {
        "content": {
            "application/json": {
                "examples": {
                    "travel_planning": {
                        "summary": "Travel Planning",
                        "description": "Automated travel planning and optimization",
                        "value": {
                            "payload": {
                                "user_id": "user-123",
                                "preferences": {
                                    "category": "travel",
                                    "timeframe": "flexible"
                                }
                            },
                            "idempotency_key": "travel-plan-123"
                        }
                    }
                }
            }
        }
    }
})
async def travel_plan(_: SimpleReq, claims: dict = Depends(verify_jwt_token)) -> EnqueuedResponse:  # noqa: B008
    return await _inline("travel.plan", {}, None)


@router.post("/calendar/organize", response_model=EnqueuedResponse, openapi_extra={
    "requestBody": {
        "content": {
            "application/json": {
                "examples": {
                    "calendar_organization": {
                        "summary": "Daily Calendar Organization",
                        "description": "Automated daily calendar organization and optimization",
                        "value": {
                            "payload": {
                                "user_id": "user-123",
                                "preferences": {
                                    "category": "calendar",
                                    "timeframe": "daily"
                                }
                            },
                            "idempotency_key": "calendar-org-123"
                        }
                    }
                }
            }
        }
    }
})
async def calendar_organize(_: SimpleReq, claims: dict = Depends(verify_jwt_token)) -> EnqueuedResponse:  # noqa: B008
    start_time = time.time()
    try:
        result = await _inline("calendar.organize_day", {}, None)
        duration = time.time() - start_time
        await track_life_metrics("calendar_organize", 200, duration)
        return result
    except Exception:
        duration = time.time() - start_time
        await track_life_metrics("calendar_organize", 500, duration)
        raise


@router.post("/shopping/optimize", response_model=EnqueuedResponse, openapi_extra={
    "requestBody": {
        "content": {
            "application/json": {
                "examples": {
                    "shopping_optimization": {
                        "summary": "Shopping Optimization",
                        "description": "Optimize shopping decisions and purchase planning",
                        "value": {
                            "payload": {
                                "user_id": "user-123",
                                "preferences": {
                                    "category": "shopping",
                                    "timeframe": "ongoing"
                                }
                            },
                            "idempotency_key": "shopping-opt-123"
                        }
                    }
                }
            }
        }
    }
})
async def shopping_optimize(_: SimpleReq, claims: dict = Depends(verify_jwt_token)) -> EnqueuedResponse:  # noqa: B008
    """
    Optimize shopping decisions and purchase planning.

    This endpoint analyzes spending patterns, identifies optimal
    purchase timing, and provides recommendations for cost savings
    and value maximization across all shopping categories.
    """
    return await _inline("shopping.optimize", {}, None)
