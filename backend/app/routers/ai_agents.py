from typing import Any

from app.agent.agent_registry import AgentName, get_registry, set_agent_config
from app.core.config import get_settings
from app.services.llm.router import LLMRouter
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ai/agents", tags=["ai-agents"])


class AgentRequest(BaseModel):
    goal: str
    context: dict[str, Any] | None = None
    agent: str | None = None  # research|writer|reviewer|planner


class AgentResponse(BaseModel):
    status: str
    message: str
    data: dict[str, Any] = {}


class AgentConfigIn(BaseModel):
    provider: str | None = None
    model: str | None = None


@router.get("/registry")
async def list_agents() -> dict[str, Any]:
    return {"agents": get_registry()}


@router.post("/{name}/config")
async def configure_agent(name: str, cfg: AgentConfigIn) -> dict[str, Any]:
    try:
        literal_name: AgentName = name  # type: ignore[assignment]
    except Exception:
        return {"ok": False, "error": "unknown agent"}
        set_agent_config(name=literal_name, provider=cfg.provider, model=cfg.model)
    return {"ok": True, "agent": name, "config": cfg.model_dump()}


@router.post("/run", response_model=AgentResponse)
async def run_agent(body: AgentRequest) -> AgentResponse:
    goal = (body.goal or "").strip()
    ctx = body.context or {}
    agent_name = (body.agent or "planner").lower()
    # Simple task planning
    if any(k in goal.lower() for k in ["investigate", "osint", "autopilot"]):
        plan = ["run autopilot", "collect artifacts", "generate report"]
    else:
        plan = ["analyze goal", "execute steps", "summarize"]

    # Choose model via LLMRouter; per-agent overrides if configured
    s = get_settings()
    router = LLMRouter(s)
    system = f"You are the {agent_name} agent. Be concise and actionable."
    try:
        summary = await router.chat(
            prompt=f"Goal: {goal}\nContext: {ctx}\nPlan: {plan}\nSummarize next steps.",
            system=system,
        )
    except Exception:
        summary = None

    return AgentResponse(status="ok", message="accepted", data={"goal": goal, "plan": plan, "summary": summary})
