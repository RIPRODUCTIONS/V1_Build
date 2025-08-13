from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class HistoricalInsights(BaseModel):
    """Aggregated insights produced by the historical data miner."""

    spending_patterns: Dict[str, Any]
    income_trends: Dict[str, Any]
    seasonal_behaviors: Dict[str, Any]
    investment_strategies: Dict[str, Any]
    productivity_correlations: Dict[str, Any]
    predictive_models: Dict[str, Any]


class BehavioralInsights(BaseModel):
    """Insights derived from user decision and behavior analysis."""

    investment_decision_quality: Dict[str, Any]
    spending_optimization: Dict[str, Any]
    optimal_schedule: Dict[str, Any]
    communication_optimization: Dict[str, Any]
    recommended_automations: List[Dict[str, Any]]


class PredictionBundle(BaseModel):
    """Collection of forward-looking predictions used by the automation engine."""

    cash_flow: Dict[str, Any]
    expenses: Dict[str, Any]
    investments: Dict[str, Any]
    productivity: Dict[str, Any]


class PredictiveAutomationPlan(BaseModel):
    """Planned pre-executed automations with confidence scores."""

    predictions: PredictionBundle
    pre_executed: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]


