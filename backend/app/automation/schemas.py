from typing import Any, Literal

from pydantic import BaseModel, Field

Priority = Literal['low', 'normal', 'high']


class AutomationSubmit(BaseModel):
    intent: str
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    priority: Priority = 'normal'


class AutomationEnqueued(BaseModel):
    status: str = 'queued'
    run_id: str


class AutomationStatus(BaseModel):
    run_id: str
    status: Literal['queued', 'running', 'succeeded', 'failed', 'compensating']
    detail: dict[str, Any] | None = None
