from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SystemHealth(BaseModel):
    component: str
    health_score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)
    performance_metrics: dict[str, float] = Field(default_factory=dict)
    last_check: datetime
    healing_attempts: int = 0


class HealingResult(BaseModel):
    success: bool
    message: str | None = None
    strategy_applied: str | None = None
    attempts: int = 0


class BuildResult(BaseModel):
    success: bool
    component: str | None = None
    performance_improvements: dict[str, float] = Field(default_factory=dict)
    message: str | None = None


