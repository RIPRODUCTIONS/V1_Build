#!/usr/bin/env python3
"""
Secure credential setup for integrations.
Run this once to configure all integrations.
"""
from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from getpass import getpass

# Add backend to path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.integrations.security import CredentialVault
from app.db import engine, Base


def setup_vault() -> CredentialVault:
    """Initialize the credential vault and DB tables."""
    Base.metadata.create_all(bind=engine)

    vault_key = os.environ.get("INTEGRATION_VAULT_KEY")
    if not vault_key:
        try:
            from cryptography.fernet import Fernet

            vault_key = Fernet.generate_key().decode()
            print(f"Generated new vault key: {vault_key}")
            print("Add this to your environment as INTEGRATION_VAULT_KEY before running the API")
            os.environ["INTEGRATION_VAULT_KEY"] = vault_key
        except Exception as exc:  # pragma: no cover - convenience path
            print(f"Failed to generate vault key: {exc}")
            sys.exit(1)
    return CredentialVault.from_env()


def setup_google_calendar(vault: CredentialVault, user_id: str) -> bool:
    print("\n=== Google Calendar Setup ===")
    print("1) Use OAuth Playground tokens (recommended for testing)")
    print("2) Use service account JSON (advanced)")
    print("3) Paste access/refresh tokens directly")
    print("4) Skip")
    choice = input("Choice (1-4): ").strip()
    if choice == "1":
        print("\nGet tokens from https://developers.google.com/oauthplayground/")
        print("Select Calendar v3 scope: https://www.googleapis.com/auth/calendar.readonly")
        access_token = getpass("Access token: ")
        refresh_token = getpass("Refresh token: ")
        if access_token and refresh_token:
            creds = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_at": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            }
            vault.put(user_id, "google_calendar", "oauth", json.dumps(creds))
            print("✅ Google Calendar configured")
            return True
    elif choice == "2":
        sa_path = input("Path to service account JSON: ").strip()
        if sa_path and Path(sa_path).exists():
            with open(sa_path, "r", encoding="utf-8") as f:
                vault.put(user_id, "google_calendar", "service_account", f.read())
            print("✅ Google Calendar configured (service account)")
            return True
    elif choice == "3":
        print("Paste tokens obtained via OAuth Playground (Settings → Use your own OAuth credentials)")
        access_token = getpass("Access token: ")
        refresh_token = getpass("Refresh token: ")
        if access_token and refresh_token:
            creds = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_at": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            }
            vault.put(user_id, "google_calendar", "oauth", json.dumps(creds))
            print("✅ Google Calendar configured (manual paste)")
            return True
    return False


def setup_openai(vault: CredentialVault, user_id: str) -> bool:
    print("\n=== OpenAI Setup ===")
    api_key = getpass("OpenAI API key (or Enter to skip): ")
    if api_key:
        vault.put(user_id, "openai", "api_key", api_key)
        print("✅ OpenAI configured")
        return True
    return False


def setup_twilio(vault: CredentialVault, user_id: str) -> bool:
    print("\n=== Twilio Setup ===")
    account_sid = input("Account SID (or Enter to skip): ").strip()
    if not account_sid:
        return False
    auth_token = getpass("Auth Token: ")
    phone = input("Twilio phone number (e.g., +1234567890): ").strip()
    vault.put(user_id, "twilio", "account_sid", account_sid)
    vault.put(user_id, "twilio", "auth_token", auth_token)
    vault.put(user_id, "twilio", "phone_number", phone)
    print("✅ Twilio configured")
    return True


def setup_notion(vault: CredentialVault, user_id: str) -> bool:
    print("\n=== Notion Setup ===")
    token = getpass("Notion integration token (or Enter to skip): ")
    if not token:
        return False
    vault.put(user_id, "notion", "token", token)
    db_id = input("Task database ID (optional): ").strip()
    if db_id:
        vault.put(user_id, "notion", "task_db_id", db_id)
    print("✅ Notion configured")
    return True


def verify_integrations(vault: CredentialVault, user_id: str) -> None:
    print("\n=== Configured Integrations ===")
    checks = [
        ("google_calendar", "oauth"),
        ("openai", "api_key"),
        ("twilio", "account_sid"),
        ("notion", "token"),
    ]
    for integ, key in checks:
        ok = bool(vault.get(user_id, integ, key))
        print(f"{'✅' if ok else '❌'} {integ}: {'Configured' if ok else 'Not configured'}")


def main() -> None:
    print("=" * 50)
    print("Integration Setup Wizard")
    print("=" * 50)
    vault = setup_vault()
    user_id = input("User ID (default: u1): ").strip() or "u1"

    configured: list[str] = []
    if setup_google_calendar(vault, user_id):
        configured.append("Google Calendar")
    if setup_openai(vault, user_id):
        configured.append("OpenAI")
    if setup_twilio(vault, user_id):
        configured.append("Twilio")
    if setup_notion(vault, user_id):
        configured.append("Notion")

    verify_integrations(vault, user_id)
    print("\n" + "=" * 50)
    print(f"Setup complete! Configured: {', '.join(configured) if configured else 'None'}")
    print("=" * 50)
    if configured:
        print("\nNext steps:")
        print("1. Set environment variable: GOOGLE_CALENDAR_SYNC=true")
        print("2. Restart your app")
        print("3. Test sync: curl -X POST http://localhost:8000/integrations/sync/" + user_id)


if __name__ == "__main__":
    main()


