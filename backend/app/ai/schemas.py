from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HistoricalAnalyzeRequest(BaseModel):
    user_id: str = Field(..., description="Target user identifier")
    years_back: int = Field(10, ge=1, le=25)
    include_sources: Optional[list[str]] = None


class BehaviorAnalyzeRequest(BaseModel):
    user_id: str
    horizon_days: int = Field(90, ge=1, le=365)
    include_dimensions: Optional[list[str]] = None


class PredictAutomateRequest(BaseModel):
    user_id: str
    pre_execute: bool = Field(True, description="Allow pre-execution of likely automations")
    dry_run: bool = Field(False, description="Only simulate without side effects")
    options: Dict[str, Any] | None = None


