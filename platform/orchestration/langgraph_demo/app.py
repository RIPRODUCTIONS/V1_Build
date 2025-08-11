from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class InputEvent(BaseModel):
    intent: str
    payload: Dict[str, Any] = {}


def planner(event: InputEvent) -> Dict[str, Any]:
    return {"plan": f"do:{event.intent}", "payload": event.payload}


def tool_executor(plan: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "ok", "echo": plan}


if __name__ == "__main__":
    sample = InputEvent(intent="demo.hello", payload={"name": "world"})
    p = planner(sample)
    out = tool_executor(p)
    print(out)


