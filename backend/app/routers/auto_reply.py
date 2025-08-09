from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auto-reply", tags=["communication"])


class Message(BaseModel):
    subject: str | None = None
    body: str


class ReplyResponse(BaseModel):
    reply: str


def simple_auto_reply(body: str) -> str:
    text = body.lower()
    if any(k in text for k in ("meeting", "schedule", "call")):
        return "Thanks for reaching out. Happy to schedule a meeting—what times work for you this week?"
    if any(k in text for k in ("invoice", "payment", "bill")):
        return "Thanks for the update. I'll review the invoice and get back to you shortly."
    if any(k in text for k in ("urgent", "asap", "immediately")):
        return "Received—I'll look into this immediately and follow up shortly."
    return "Thanks for your message—appreciate it. I’ll get back to you soon."


@router.post("/suggest", response_model=ReplyResponse)
def suggest(message: Message) -> ReplyResponse:
    if not message.body or not message.body.strip():
        raise HTTPException(status_code=400, detail="body is required")
    return ReplyResponse(reply=simple_auto_reply(message.body))
