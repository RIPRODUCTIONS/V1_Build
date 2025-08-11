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
    "IdeaDiscovered",
    "ResearchCompleted",
    "PlanApproved",
    "BuildArtifact",
    "TestReport",
    "DeployRequested",
]
