from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ai/agents", tags=["ai-agents"])


class AgentRequest(BaseModel):
    goal: str
    context: dict[str, Any] | None = None


class AgentResponse(BaseModel):
    status: str
    message: str
    data: dict[str, Any] = {}


@router.post("/run", response_model=AgentResponse)
async def run_agent(body: AgentRequest) -> AgentResponse:
    return AgentResponse(status="ok", message="accepted", data={"goal": body.goal})
