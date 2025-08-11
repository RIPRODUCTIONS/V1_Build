from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class InputEvent(BaseModel):
    intent: str
    payload: dict[str, Any] = {}


def planner(event: InputEvent) -> dict[str, Any]:
    return {"plan": f"do:{event.intent}", "payload": event.payload}


def tool_executor(plan: dict[str, Any]) -> dict[str, Any]:
    return {"status": "ok", "echo": plan}


if __name__ == "__main__":
    sample = InputEvent(intent="demo.hello", payload={"name": "world"})
    p = planner(sample)
    out = tool_executor(p)
    print(out)
