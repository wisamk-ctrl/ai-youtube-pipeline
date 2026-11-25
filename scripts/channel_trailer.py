"""Upload the channel trailer and make it what non-subscribers see first on the channel page.

usage: python scripts/channel_trailer.py <video.mp4>

Founder 2026-11-25: "upload it as the channel trailer". The video goes up public (a channel trailer must be
public), disclosed as synthetic media (the presenter is the AI digital twin), then
brandingSettings.channel.unsubscribedTrailer is set; every other branding setting is sent back unchanged.
The trailer is read back afterwards: YouTube has ignored this field for some channels, and then the last
step stays manual (YouTube Studio → Customisation → Home tab → Channel trailer)."""
from __future__ import annotations

import copy
import os
import sys
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
API = "https://www.googleapis.com/youtube/v3"
TITLE = "AI This Week | AI news for decision-makers in the Gulf, the Levant, Türkiye and Africa"
DESCRIPTION = """AI news moves fast. Most of it misses what it means for our region.

Every Sunday, in about fifteen minutes: what happened (a source for every fact), what it means for your business, your team and your market, and the view of Wissam Kishek, from 25 years of selling technology and leading teams across this region. When news breaks, a Short the same day.

Presented by Wissam Kishek's AI digital twin, with his consent.
Information only, not investment advice.

Subscribe: {channel}
"""


def video_body(cfg: dict[str, Any]) -> dict[str, Any]:
    p = cfg.get("publish", {})
    return {"snippet": {"title": TITLE, "description": DESCRIPTION.format(channel=p.get("channel_url", "")).strip(),
                        "tags": list(p.get("tags_en", []))[:30], "categoryId": "28",
                        "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}


def with_trailer(branding: dict[str, Any], video_id: str) -> dict[str, Any]:
    out = copy.deepcopy(branding)
    out.setdefault("channel", {})["unsubscribedTrailer"] = video_id
    return out


def token() -> str:
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    r.raise_for_status()
    return r.json()["access_token"]


def upload(video: Path, body: dict[str, Any], h: dict[str, str]) -> str:
    start = requests.post("https://www.googleapis.com/upload/youtube/v3/videos", headers={**h, "X-Upload-Content-Type": "video/mp4"},
                          params={"uploadType": "resumable", "part": "snippet,status"}, json=body, timeout=60)
    start.raise_for_status()
    with video.open("rb") as f:
        done = requests.put(start.headers["Location"], headers={**h, "Content-Type": "video/mp4"}, data=f, timeout=1800)
    done.raise_for_status()
    return done.json()["id"]


def main(argv: list[str]) -> int:
    from pipeline.config import load_settings
    video = Path(argv[1])
    h = {"Authorization": f"Bearer {token()}"}
    ch = requests.get(f"{API}/channels", headers=h, timeout=30, params={"part": "snippet,brandingSettings", "mine": "true"})
    ch.raise_for_status()
    items = ch.json().get("items") or []
    if not items:
        print("No channel on this sign-in")
        return 1
    me = items[0]
    print(f"Channel: {me['snippet']['title']}")
    vid = upload(video, video_body(load_settings()), h)
    print(f"Uploaded https://youtu.be/{vid} (public)")
    put = requests.put(f"{API}/channels", headers=h, timeout=30, params={"part": "brandingSettings"},
                       json={"id": me["id"], "brandingSettings": with_trailer(me.get("brandingSettings", {}), vid)})
    if put.status_code >= 400:
        print(f"Trailer not set: {put.status_code} {put.text[:300]}")
        return 1
    back = requests.get(f"{API}/channels", headers=h, timeout=30, params={"part": "brandingSettings", "id": me["id"]}).json()
    got = ((back.get("items") or [{}])[0].get("brandingSettings", {}).get("channel", {}) or {}).get("unsubscribedTrailer")
    if got != vid:
        print(f"YouTube did not keep the trailer setting (reads back {got!r}): set https://youtu.be/{vid} by hand in "
              "YouTube Studio → Customisation → Home tab → Channel trailer")
        return 2
    print(f"Channel trailer set: https://youtu.be/{vid}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
