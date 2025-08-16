from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HistoricalInsights(BaseModel):
    """Aggregated insights produced by the historical data miner."""

    spending_patterns: dict[str, Any]
    income_trends: dict[str, Any]
    seasonal_behaviors: dict[str, Any]
    investment_strategies: dict[str, Any]
    productivity_correlations: dict[str, Any]
    predictive_models: dict[str, Any]


class BehavioralInsights(BaseModel):
    """Insights derived from user decision and behavior analysis."""

    investment_decision_quality: dict[str, Any]
    spending_optimization: dict[str, Any]
    optimal_schedule: dict[str, Any]
    communication_optimization: dict[str, Any]
    recommended_automations: list[dict[str, Any]]


class PredictionBundle(BaseModel):
    """Collection of forward-looking predictions used by the automation engine."""

    cash_flow: dict[str, Any]
    expenses: dict[str, Any]
    investments: dict[str, Any]
    productivity: dict[str, Any]


class PredictiveAutomationPlan(BaseModel):
    """Planned pre-executed automations with confidence scores."""

    predictions: PredictionBundle
    pre_executed: list[dict[str, Any]]
    confidence_scores: dict[str, float]


