from __future__ import annotations

from typing import Literal

from app.routers.auto_reply import simple_auto_reply
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/comm", tags=["communication"])


class AutoReplyRequest(BaseModel):
    channel: Literal["email", "sms"] = Field(default="email")
    subject: str | None = None
    body: str


class AutoReplyResponse(BaseModel):
    reply: str


@router.post("/auto_reply", response_model=AutoReplyResponse)
async def auto_reply(req: AutoReplyRequest) -> AutoReplyResponse:
    if not req.body or not req.body.strip():
        raise HTTPException(status_code=400, detail="Body is required")
    # Deterministic reply using existing heuristic; LLM can be wired later
    r = simple_auto_reply(req.body)
    return AutoReplyResponse(reply=r)
