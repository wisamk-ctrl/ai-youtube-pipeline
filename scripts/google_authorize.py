#!/usr/bin/env python3
"""
One-time: obtain a Google refresh token for Gmail or YouTube.

    GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... python scripts/google_authorize.py gmail
    GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... python scripts/google_authorize.py youtube

Opens a browser for consent, then prints the refresh token to paste into .env /
GitHub secrets. Run it on a machine with a browser (your Mac), not in CI.
Setup in Google Cloud Console first: enable the Gmail API and YouTube Data API v3,
create an OAuth client of type "Desktop app", and add yourself as a test user
(or publish the consent screen so the token doesn't expire after 7 days).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402

from pipeline.google_auth import SCOPES, TOKEN_ENV  # noqa: E402


def main() -> None:
    service = sys.argv[1] if len(sys.argv) > 1 else ""
    if service not in SCOPES:
        sys.exit("usage: google_authorize.py gmail|youtube")
    flow = InstalledAppFlow.from_client_config(
        {"installed": {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }},
        scopes=SCOPES[service],
    )
    # access_type=offline + prompt=consent forces Google to issue a refresh token.
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    print(f"\n{TOKEN_ENV[service]}={creds.refresh_token}\n")


if __name__ == "__main__":
    main()
