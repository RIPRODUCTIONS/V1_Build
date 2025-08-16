from __future__ import annotations

from typing import Any, Dict, List

import smtplib
from email.mime.text import MIMEText

import httpx
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from app.middleware.auth import validate_api_key

from app.core.config import get_settings


router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(validate_api_key)])


async def _post_webhook(url: str, payload: Dict[str, Any]) -> None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload)
    except Exception:
        # best effort
        pass


def _send_email(subject: str, body: str) -> None:
    s = get_settings()
    if not (s.email_smtp_host and s.email_from and s.email_to):
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = s.email_from  # type: ignore[assignment]
        msg["To"] = s.email_to  # type: ignore[assignment]
        with smtplib.SMTP(s.email_smtp_host, s.email_smtp_port or 25) as server:  # type: ignore[arg-type]
            if s.email_username and s.email_password:
                server.starttls()
                server.login(s.email_username, s.email_password)
            server.sendmail(s.email_from, [s.email_to], msg.as_string())  # type: ignore[arg-type]
    except Exception:
        # best effort
        pass


@router.post("/prometheus")
async def receive_prometheus_alerts(request: Request) -> Dict[str, Any]:
    s = get_settings()
    body = await request.json()
    alerts: List[Dict[str, Any]] = list(body.get("alerts") or [])
    summary_lines: List[str] = []
    for a in alerts[:20]:
        status = str(a.get("status") or "")
        labels = a.get("labels") or {}
        annotations = a.get("annotations") or {}
        name = labels.get("alertname") or labels.get("alert_name") or "alert"
        desc = annotations.get("description") or annotations.get("summary") or ""
        summary_lines.append(f"[{status}] {name} - {desc}")
    summary = "\n".join(summary_lines) if summary_lines else "(no alerts)"

    payload = {
        "source": "prometheus",
        "count": len(alerts),
        "summary": summary,
    }
    # Webhooks
    if s.slack_webhook_url:
        await _post_webhook(s.slack_webhook_url, {"text": summary})  # type: ignore[arg-type]
    if s.alert_webhook_url:
        await _post_webhook(s.alert_webhook_url, payload)  # type: ignore[arg-type]
    # Email
    _send_email(subject="Builder Alerts", body=summary)
    return {"status": "ok", "received": len(alerts)}


@router.post("/test")
async def send_test_alert(request: Request, payload: Dict[str, Any] | None = None, x_api_key: str | None = Header(default=None)) -> Dict[str, Any]:
    """Send a synthetic alert via configured channels. Requires X-API-Key when SECURE_MODE=true."""
    import os as _os
    if (_os.getenv("SECURE_MODE", "false").lower() == "true"):
        token = request.query_params.get("token")
        header_or_token = x_api_key or token
        # Reuse centralized validator for consistency
        await validate_api_key(header_or_token)
    body = payload or {}
    msg = str(body.get("message") or "Synthetic alert from Builder")
    s = get_settings()
    if s.slack_webhook_url:
        await _post_webhook(s.slack_webhook_url, {"text": msg})  # type: ignore[arg-type]
    if s.alert_webhook_url:
        await _post_webhook(s.alert_webhook_url, {"text": msg, "source": "synthetic"})  # type: ignore[arg-type]
    _send_email(subject="Builder Test Alert", body=msg)
    return {"status": "ok", "sent": True}


