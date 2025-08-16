from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.db import SessionLocal
from app.models import AgentConfigKV

AgentName = Literal[
    "research",
    "writer",
    "reviewer",
    "planner",
]


@dataclass
class AgentConfig:
    provider: str | None  # lmstudio|ollama|vllm|openai|anthropic|None -> use primary
    model: str | None     # model name per provider; None -> use default from settings


# Default in-memory registry. This can be persisted later if needed.
_REGISTRY: dict[AgentName, AgentConfig] = {
    "research": AgentConfig(provider=None, model=None),
    "writer": AgentConfig(provider=None, model=None),
    "reviewer": AgentConfig(provider=None, model=None),
    "planner": AgentConfig(provider=None, model=None),
}


def get_registry() -> dict[str, dict]:
    # Return as JSON-serializable structure
    return {str(name): {"provider": cfg.provider, "model": cfg.model} for name, cfg in _REGISTRY.items()}


def set_agent_config(name: AgentName, provider: str | None, model: str | None) -> None:
    if name not in _REGISTRY:
        raise ValueError("unknown agent name")
    if provider is not None and provider not in {"lmstudio", "ollama", "vllm", "openai", "anthropic"}:
        raise ValueError("unsupported provider")
    _REGISTRY[name] = AgentConfig(provider=provider, model=model)
    # Persist to DB
    try:
        db = SessionLocal()
        try:
            rec = db.query(AgentConfigKV).filter(AgentConfigKV.name == name).first()
            if not rec:
                rec = AgentConfigKV(name=name, provider=provider, model=model, updated_at=datetime.now(timezone.utc))
            else:
                rec.provider = provider
                rec.model = model
                rec.updated_at = datetime.now(timezone.utc)
            db.add(rec)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass


def get_agent_config(name: AgentName) -> AgentConfig:
    return _REGISTRY[name]


def load_agent_configs_from_db() -> None:
    try:
        db = SessionLocal()
        try:
            rows = db.query(AgentConfigKV).all()
            for r in rows:
                try:
                    name_literal: AgentName = r.name  # type: ignore[assignment]
                except Exception:
                    continue
                if name_literal in _REGISTRY:
                    _REGISTRY[name_literal] = AgentConfig(provider=r.provider, model=r.model)
        finally:
            db.close()
    except Exception:
        pass



