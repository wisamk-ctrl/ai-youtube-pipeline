"""
Google OAuth for the Gmail source (Phase 1) and the YouTube publisher (Phase 5).

One OAuth "Desktop app" client in Google Cloud serves both. Each API gets its own
refresh token (different scopes), obtained once with scripts/google_authorize.py
and stored as a secret:

    GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET      the OAuth client
    GMAIL_REFRESH_TOKEN                          scope gmail.readonly
    YOUTUBE_REFRESH_TOKEN                        scope youtube.upload

Refresh tokens don't expire while the app is in "production" in the OAuth
consent screen; in "testing" mode Google revokes them after 7 days.
"""

from __future__ import annotations

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from pipeline.config import require_env

SCOPES = {
    "gmail": ["https://www.googleapis.com/auth/gmail.readonly"],
    "youtube": ["https://www.googleapis.com/auth/youtube.upload"],
}
TOKEN_ENV = {"gmail": "GMAIL_REFRESH_TOKEN", "youtube": "YOUTUBE_REFRESH_TOKEN"}


def credentials(service: str) -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=require_env(TOKEN_ENV[service]),
        client_id=require_env("GOOGLE_CLIENT_ID"),
        client_secret=require_env("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES[service],
    )
    creds.refresh(Request())  # exchange the refresh token for a short-lived access token
    return creds


def client(service: str):
    api, version = {"gmail": ("gmail", "v1"), "youtube": ("youtube", "v3")}[service]
    return build(api, version, credentials=credentials(service), cache_discovery=False)
