from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import get_settings
from app.core.dlq import DeadLetterQueue
from app.integrations.security import CredentialVault
from app.integrations.sync_models import GmailWatchSubscription


@dataclass(slots=True)
class GmailWebhookHandler:
    dlq: DeadLetterQueue
    settings: Any
    vault: CredentialVault

    def __init__(self) -> None:
        self.dlq = DeadLetterQueue()
        self.settings = get_settings()
        self.vault = CredentialVault.from_env()

    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        # constant-time compare
        return hmac.compare_digest(mac, signature or "")

    async def setup_gmail_watch(self, user_id: str, user_email: str) -> str | None:
        """Create Gmail watch subscription via watch API.
        NOTE: Requires Pub/Sub in production; for HTTP-style webhook, we simulate by hitting our endpoint.
        """
        # Placeholder flow: store a synthetic watch with expiration to enable local e2e without Pub/Sub
        db = __import__("app.db").db.SessionLocal()
        row = db.get(GmailWatchSubscription, user_id)
        if row is None:
            row = GmailWatchSubscription(user_id=user_id, watch_id="local-watch", history_id=None, expiration=datetime.now(UTC) + timedelta(days=1), webhook_url=f"{self.settings.WEBHOOK_BASE_URL}/webhooks/gmail")
            db.add(row)
        else:
            row.watch_id = "local-watch"
            row.expiration = datetime.now(UTC) + timedelta(days=1)
            row.webhook_url = f"{self.settings.WEBHOOK_BASE_URL}/webhooks/gmail"
        db.commit()
        db.close()
        return "local-watch"

    async def process_gmail_history(self, user_id: str, start_history_id: str | None) -> str | None:
        """Call Gmail history.list incrementally and process changes.
        Returns latest historyId on success.
        """
        # Minimal implementation with placeholders to avoid token need now
        # Extend later to call https://gmail.googleapis.com/gmail/v1/users/me/history
        return start_history_id

    async def update_history_state(self, user_id: str, new_history_id: str | None) -> None:
        db = __import__("app.db").db.SessionLocal()
        row = db.get(GmailWatchSubscription, user_id)
        if row is None:
            row = GmailWatchSubscription(user_id=user_id, watch_id="local-watch", history_id=None, expiration=datetime.now(UTC) + timedelta(days=1), webhook_url=f"{self.settings.WEBHOOK_BASE_URL}/webhooks/gmail")
            db.add(row)
        row.history_id = int(new_history_id) if (new_history_id and str(new_history_id).isdigit()) else row.history_id
        db.commit()
        db.close()

    async def renew_gmail_watch(self, user_id: str) -> bool:
        db = __import__("app.db").db.SessionLocal()
        row = db.get(GmailWatchSubscription, user_id)
        if not row:
            db.close()
            return False
        row.expiration = datetime.now(UTC) + timedelta(days=1)
        db.commit()
        db.close()
        return True

    async def handle_webhook_error(self, error: Exception, payload: dict[str, Any], user_id: str) -> None:
        await self.dlq.send_to_dlq("gmail_webhooks", payload, error, context={"user_id": user_id})


