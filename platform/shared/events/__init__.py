from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_type: str = Field(..., description="Event type identifier")
    version: str = Field(default="v1")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AutomationRunRequested(DomainEvent):
    event_type: str = Field(default="automation.run.requested")
    intent: str
    payload: dict = Field(default_factory=dict)
    idempotency_key: str | None = None
    subject: str | None = None
    correlation_id: str | None = None


class RunStatusUpdated(DomainEvent):
    event_type: str = Field(default="run.status.updated")
    run_id: str
    status: str
    intent: str | None = None
    department: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunStarted(DomainEvent):
    event_type: str = Field(default="run.started")
    run_id: str
    intent: str
    department: str | None = None
    correlation_id: str | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)


class RunCompleted(DomainEvent):
    event_type: str = Field(default="run.completed")
    run_id: str
    intent: str
    department: str | None = None
    correlation_id: str | None = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    result: dict[str, Any] = Field(default_factory=dict)


class RunFailed(DomainEvent):
    event_type: str = Field(default="run.failed")
    run_id: str
    intent: str
    department: str | None = None
    correlation_id: str | None = None
    failed_at: datetime = Field(default_factory=datetime.utcnow)
    error: str
    error_details: dict[str, Any] = Field(default_factory=dict)


class RunLogEntry(DomainEvent):
    event_type: str = Field(default="run.log")
    run_id: str
    level: str = Field(..., description="log, warn, error, debug")
    message: str
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IdeaDiscovered(DomainEvent):
    event_type: str = Field(default="idea.discovered")
    idea_id: str
    summary: str


class ResearchCompleted(DomainEvent):
    event_type: str = Field(default="research.completed")
    idea_id: str
    findings: dict


class PlanApproved(DomainEvent):
    event_type: str = Field(default="plan.approved")
    plan_id: str
    steps: list[str] = Field(default_factory=list)


class BuildArtifact(DomainEvent):
    event_type: str = Field(default="build.artifact")
    artifact_id: str
    uri: str


class TestReport(DomainEvent):
    event_type: str = Field(default="test.report")
    artifact_id: str
    passed: bool
    details: dict = Field(default_factory=dict)


class DeployRequested(DomainEvent):
    event_type: str = Field(default="deploy.requested")
    artifact_id: str
    environment: str = Field(default="dev")


__all__ = [
    "DomainEvent",
    "AutomationRunRequested",
    "RunStatusUpdated",
    "RunStarted",
    "RunCompleted",
    "RunFailed",
    "RunLogEntry",
    "IdeaDiscovered",
    "ResearchCompleted",
    "PlanApproved",
    "BuildArtifact",
    "TestReport",
    "DeployRequested",
]
