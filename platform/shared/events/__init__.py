from __future__ import annotations

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_type: str = Field(..., description="Event type identifier")
    version: str = Field(default="v1")


class AutomationRunRequested(DomainEvent):
    event_type: str = Field(default="automation.run.requested")
    intent: str
    payload: dict = Field(default_factory=dict)
    idempotency_key: str | None = None


__all__ = [
    "DomainEvent",
    "AutomationRunRequested",
]



