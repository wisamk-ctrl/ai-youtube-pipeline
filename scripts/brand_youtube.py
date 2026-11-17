"""Set the YouTube channel banner from assets/brand/ (the one artwork every channel uses).

The profile picture cannot be set by an app (YouTube offers no API for it): that stays a manual step
in YouTube Studio → Customisation → Branding, with assets/brand/logo_800.png.
Everything else in the channel's branding settings is sent back unchanged."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
BANNER = ROOT / "assets" / "brand" / "youtube_banner_2560x1440.png"
API = "https://www.googleapis.com/youtube/v3"


def token() -> str:
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    r.raise_for_status()
    return r.json()["access_token"]


def main() -> int:
    h = {"Authorization": f"Bearer {token()}"}
    ch = requests.get(f"{API}/channels", headers=h, timeout=30, params={"part": "snippet,brandingSettings", "mine": "true"})
    ch.raise_for_status()
    items = ch.json().get("items") or []
    if not items:
        print("No channel on this sign-in")
        return 1
    me = items[0]
    print(f"Channel: {me['snippet']['title']}")
    up = requests.post("https://www.googleapis.com/upload/youtube/v3/channelBanners/insert", headers={**h, "Content-Type": "image/png"},
                       params={"uploadType": "media"}, data=BANNER.read_bytes(), timeout=120)
    if up.status_code >= 400:
        print(f"Banner upload refused: {up.status_code} {up.text[:300]}")
        return 1
    branding = me.get("brandingSettings", {})
    branding.setdefault("image", {})["bannerExternalUrl"] = up.json()["url"]
    done = requests.put(f"{API}/channels", headers=h, timeout=30, params={"part": "brandingSettings"},
                        json={"id": me["id"], "brandingSettings": branding})
    if done.status_code >= 400:
        print(f"Banner not set: {done.status_code} {done.text[:300]}")
        return 1
    print("Banner set from assets/brand/youtube_banner_2560x1440.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
