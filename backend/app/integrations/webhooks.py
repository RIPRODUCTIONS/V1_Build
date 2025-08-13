from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request
from app.integrations.google.gmail_webhooks import GmailWebhookHandler

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/slack")
async def slack_webhook(request: Request, x_slack_signature: str | None = Header(default=None)):
    # TODO: validate signature
    payload = await request.json()
    return {"status": "ok"}


@router.post("/github")
async def github_webhook(request: Request, x_hub_signature_256: str | None = Header(default=None)):
    payload = await request.json()
    return {"status": "ok"}


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    return {"status": "ok"}


@router.post("/gmail")
async def gmail_webhook(request: Request, x_signature: str | None = Header(default=None)):
    payload_bytes = await request.body()
    # Optional signature verification using GMAIL_WEBHOOK_SECRET
    secret = __import__("os").getenv("GMAIL_WEBHOOK_SECRET", "test-secret")
    handler = GmailWebhookHandler()
    if secret and not handler.verify_webhook_signature(payload_bytes, x_signature or "", secret):
        raise HTTPException(status_code=401, detail="invalid signature")
    try:
        data = await request.json()
    except Exception:
        data = {}
    # In real Gmail push, payload would contain historyId and email; here support test shim
    user_id = str(data.get("user_id") or "1")
    history_id = data.get("historyId")
    # Fire-and-forget processing; ack immediately
    __import__("asyncio").create_task(handler.process_gmail_history(user_id, history_id))
    return {"status": "ok"}

