from __future__ import annotations

from celery import shared_task

from app.integrations.hub import IntegrationHub
from app.integrations.google_workspace import (
    GoogleCalendarIntegration,
    GmailIntegration,
    GoogleDriveIntegration,
)

hub = IntegrationHub()
hub.register("google_calendar", GoogleCalendarIntegration())
hub.register("gmail", GmailIntegration())
hub.register("google_drive", GoogleDriveIntegration())


@shared_task(name="integrations.sync_integration")
def sync_integration(user_id: str, integration_name: str) -> dict:
    integ = hub.integrations.get(integration_name)
    if not integ:
        return {"status": "not_found", "integration": integration_name}
    return hub.integrations[integration_name].__class__.__name__  # type: ignore


@shared_task(name="integrations.discover_new_integrations")
def discover_new_integrations(user_id: str) -> list:
    from asgiref.sync import async_to_sync

    return async_to_sync(hub.auto_discover)(user_id)


@shared_task(name="integrations.sync_user_all")
def sync_user_all(user_id: str) -> dict:
    """Synchronously sync all integrations for a user.

    Returns a mapping of integration -> result dict.
    """
    from asgiref.sync import async_to_sync

    return async_to_sync(hub.sync_all)(user_id)


@shared_task(name="integrations.refresh_expiring_tokens")
def refresh_expiring_tokens() -> dict:
    # Placeholder; actual implementation will scan vault for expiring tokens
    return {"status": "ok"}


@shared_task(name="integrations.cleanup_stale_webhooks")
def cleanup_stale_webhooks() -> dict:
    return {"status": "ok"}


