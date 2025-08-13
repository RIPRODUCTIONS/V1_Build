from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional
import uuid
import re

import httpx
import jinja2

from sqlalchemy.orm import Session

from app.models import Task
from app.automations.models import Notification
from app.integrations.security import CredentialVault


class ActionExecutor:
    def __init__(self):
        self.jinja = jinja2.Environment(autoescape=True)
        self.vault: Optional[CredentialVault] = None
        self._actions = {
            "create_task": self.create_task,
            "send_notification": self.send_notification,
            "aggregate_and_notify": self.aggregate_and_notify,
            "send_email": self.send_email,
            "send_slack": self.send_slack,
            "send_sms": self.send_sms,
        }

    async def execute(self, action_type: str, params: dict, context: dict, db: Session) -> dict:
        if action_type not in self._actions:
            raise ValueError(f"Unknown action: {action_type}")
        return await self._actions[action_type](params, context, db)

    async def create_task(self, params: dict, context: dict, db: Session) -> dict:
        raw_user = context.get("user_id")
        try:
            owner_id = int(raw_user) if isinstance(raw_user, (str, int)) and str(raw_user).isdigit() else 1
        except Exception:
            owner_id = 1
        event = context.get("event", {})
        title_tmpl = params.get("title_template")
        title = (
            self.render_template(title_tmpl, {"event": event}) if title_tmpl else params.get("title", "Untitled Task")
        )
        task = Task(owner_id=owner_id, lead_id=None, title=title)
        db.add(task)
        db.commit()
        db.refresh(task)
        return {"task_id": task.id}

    async def send_notification(self, params: dict, context: dict, db: Session) -> dict:
        # Keep existing channel handling but default to in-app email log
        channel = params.get("channel", "email")
        message = params.get("message", "Automation notification")
        subject = params.get("subject", None)
        notif = Notification(
            id=str(uuid.uuid4()),
            user_id=str(context.get("user_id")),
            channel=channel,
            subject=subject,
            message=message,
            sent_at=datetime.utcnow(),
            metadata={"rule_id": context.get("rule_id")},
        )
        db.add(notif)
        db.commit()
        return {"sent": True, "channel": channel, "notification_id": notif.id}

    async def aggregate_and_notify(self, params: dict, context: dict, db: Session) -> dict:
        user_id = context.get("user_id")
        # Placeholder aggregation — extend with real sources
        message = "No events or tasks for today"
        return await self.send_notification({"message": message, "channel": params.get("channel", "email"), "subject": "Daily Summary"}, context, db)

    async def send_notification(self, params: dict, context: dict, db: Session) -> dict:
        channel = params.get("channel", "email")
        if channel == "slack":
            return await self.send_slack(params, context, db)
        if channel == "sms":
            return await self.send_sms(params, context, db)
        return await self.send_email(params, context, db)

    def _get_vault(self) -> Optional[CredentialVault]:
        if self.vault is None:
            try:
                self.vault = CredentialVault.from_env()
            except Exception:
                self.vault = None
        return self.vault

    async def send_email(self, params: dict, context: dict, db: Session) -> dict:
        subject = params.get("subject", "Automation Notification")
        message = params.get("message", "")
        notif = Notification(
            id=str(uuid.uuid4()),
            user_id=str(context.get("user_id")),
            channel="email",
            subject=subject,
            message=message,
            sent_at=datetime.utcnow(),
            metadata={"rule_id": context.get("rule_id")},
        )
        db.add(notif)
        db.commit()
        return {"sent": True, "channel": "email", "notification_id": notif.id}

    async def send_slack(self, params: dict, context: dict, db: Session) -> dict:
        message = params.get("message", "Automation notification")
        vault = self._get_vault()
        webhook_url = None
        if vault:
            webhook_url = vault.get(str(context.get("user_id")), "slack", "webhook_url")
        if webhook_url:
            try:
                async with httpx.AsyncClient(timeout=6) as client:
                    resp = await client.post(webhook_url, json={"text": message})
                    return {"sent": resp.status_code == 200, "status": resp.status_code, "channel": "slack"}
            except Exception:
                return {"sent": False, "channel": "slack", "error": "send_failed"}
        # store a log notification if no webhook
        notif = Notification(
            id=str(uuid.uuid4()),
            user_id=str(context.get("user_id")),
            channel="slack",
            subject=None,
            message=message,
            sent_at=datetime.utcnow(),
            metadata={"rule_id": context.get("rule_id"), "note": "webhook_missing"},
        )
        db.add(notif)
        db.commit()
        return {"sent": False, "channel": "slack", "notification_id": notif.id}

    async def send_sms(self, params: dict, context: dict, db: Session) -> dict:
        # Simulate SMS; integrate Twilio later
        notif = Notification(
            id=str(uuid.uuid4()),
            user_id=str(context.get("user_id")),
            channel="sms",
            subject=None,
            message=params.get("message", ""),
            sent_at=datetime.utcnow(),
            metadata={"rule_id": context.get("rule_id")},
        )
        db.add(notif)
        db.commit()
        return {"sent": True, "channel": "sms", "notification_id": notif.id}

    def render_template(self, template: str, ctx: dict) -> str:
        try:
            return self.jinja.from_string(template).render(**ctx)
        except Exception:
            return template


