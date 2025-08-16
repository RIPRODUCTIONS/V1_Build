from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HistoricalAnalyzeRequest(BaseModel):
    user_id: str = Field(..., description="Target user identifier")
    years_back: int = Field(10, ge=1, le=25)
    include_sources: list[str] | None = None


class BehaviorAnalyzeRequest(BaseModel):
    user_id: str
    horizon_days: int = Field(90, ge=1, le=365)
    include_dimensions: list[str] | None = None


class PredictAutomateRequest(BaseModel):
    user_id: str
    pre_execute: bool = Field(True, description="Allow pre-execution of likely automations")
    dry_run: bool = Field(False, description="Only simulate without side effects")
    options: dict[str, Any] | None = None


