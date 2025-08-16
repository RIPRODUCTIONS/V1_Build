import logging
import os
from typing import Any, TypedDict

import httpx

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")


async def send_notification(title: str, message: str, level: str = "info", extra: dict[str, Any] | None = None) -> None:
    """Send a notification to Slack if configured; otherwise log.

    Args:
        title: Notification title
        message: Main message text
        level: 'info' | 'warning' | 'error'
        extra: Optional extra fields
    """
    class ContextElement(TypedDict, total=False):
        type: str
        text: dict[str, str]

    class SlackPayload(TypedDict, total=False):
        text: str
        blocks: list[dict[str, Any]]

    payload: SlackPayload = {
        "text": f"*{title}*\n{message}",
    }
    if extra:
        payload["blocks"] = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{title}*\n{message}"},
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"```{extra}```"}],
            },
        ]

    if SLACK_WEBHOOK_URL:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(SLACK_WEBHOOK_URL, json=payload)
            return
        except Exception as e:
            logger.warning(f"Slack notification failed: {e}")

    # Fallback to logs
    log = getattr(logger, level, logger.info)
    log(f"NOTIFY: {title} - {message} - extra={extra}")



