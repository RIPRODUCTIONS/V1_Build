#!/usr/bin/env python3
"""
Helper to print Google OAuth Playground instructions and collect tokens.
"""
from __future__ import annotations

import json
from getpass import getpass

SCOPES = {
    "calendar_readonly": [
        "https://www.googleapis.com/auth/calendar.readonly",
    ],
    "google_full_test": [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ],
}

def main() -> None:
    print("Google OAuth Playground helper")
    print("1) Open https://developers.google.com/oauthplayground")
    print("2) Click the gear (top right): Enable 'Use your own OAuth credentials' and paste your CLIENT_ID/CLIENT_SECRET")
    print("3) In Step 1, paste one scope per line, e.g.:")
    for s in SCOPES["calendar_readonly"]:
        print("   ", s)
    print("4) Authorize APIs → Step 2: Exchange authorization code for tokens")
    print("5) Copy access_token and refresh_token below")

    access = getpass("access_token: ")
    refresh = getpass("refresh_token: ")
    out = {"access_token": access, "refresh_token": refresh}
    print(json.dumps(out))

if __name__ == "__main__":
    main()


