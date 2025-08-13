from __future__ import annotations

from fastapi import APIRouter, Depends
from typing import Any, Dict

from app.security.deps import require_scopes
from app.security.scopes import WRITE_AI, READ_LEADS
from .models import HistoricalInsights, BehavioralInsights, PredictiveAutomationPlan, PredictionBundle
from .schemas import HistoricalAnalyzeRequest, BehaviorAnalyzeRequest, PredictAutomateRequest
from .engines import HistoricalDataMiner, BehaviorAnalysisEngine, PredictiveAutomationEngine


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/historical/ingest_and_analyze",
    response_model=HistoricalInsights,
)
async def ingest_and_analyze_historical(req: HistoricalAnalyzeRequest | None = None, user=Depends(require_scopes({READ_LEADS}))) -> HistoricalInsights:
    miner = HistoricalDataMiner()
    user_id = (req.user_id if req else "anonymous")
    years_back = (req.years_back if req else 10)
    include_sources = (req.include_sources if req else None)
    return await miner.ingest_and_analyze(user_id=user_id, years_back=years_back, include_sources=include_sources)


@router.post(
    "/behavior/analyze",
    response_model=BehavioralInsights,
)
async def analyze_behavior(req: BehaviorAnalyzeRequest | None = None, user=Depends(require_scopes({WRITE_AI}))) -> BehavioralInsights:
    engine = BehaviorAnalysisEngine()
    user_id = (req.user_id if req else "anonymous")
    horizon_days = (req.horizon_days if req else 90)
    include_dimensions = (req.include_dimensions if req else None)
    return await engine.analyze(user_id=user_id, horizon_days=horizon_days, include_dimensions=include_dimensions)


@router.post(
    "/predict/automate",
    response_model=PredictiveAutomationPlan,
)
async def predict_and_automate(req: PredictAutomateRequest | None = None, user=Depends(require_scopes({WRITE_AI}))) -> PredictiveAutomationPlan:
    engine = PredictiveAutomationEngine()
    user_id = (req.user_id if req else "anonymous")
    pre_execute = (req.pre_execute if req else True)
    options = (req.options if req else None)
    return await engine.predict_and_plan(user_id=user_id, pre_execute=pre_execute, options=options)


