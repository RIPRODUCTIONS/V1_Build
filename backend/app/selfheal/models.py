from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SystemHealth(BaseModel):
    component: str
    health_score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    last_check: datetime
    healing_attempts: int = 0


class HealingResult(BaseModel):
    success: bool
    message: Optional[str] = None
    strategy_applied: Optional[str] = None
    attempts: int = 0


class BuildResult(BaseModel):
    success: bool
    component: Optional[str] = None
    performance_improvements: Dict[str, float] = Field(default_factory=dict)
    message: Optional[str] = None


