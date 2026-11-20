"""Daily channel-integrity check (founder 2026-11-20: "I'm concerned about somebody hijacking the account").

A hijacked YouTube channel is typically renamed, its handle and description changed, old videos hidden and scam
uploads (fake live streams) added within hours. Once a day this compares the channel with data/integrity.json
(yesterday's snapshot) and with the video IDs the pipeline itself published (data/ and reviewed/). Anything else is
an alert: one open "Security: channel changed" issue, plus a WhatsApp message when CallMeBot is set up.
After alerting, the snapshot moves on, so each change is reported once.

What it cannot see: who the channel managers are, sign-ins, or changes to the Google account. Those need the
founder's own protection (passkeys / Advanced Protection; see docs/SECURITY.md).

Usage: python scripts/integrity.py   (needs GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
STATE = ROOT / "data" / "integrity.json"
_YT_ID = re.compile(r"(?:youtu\.be/|shorts/|watch\?v=|video_?id[\"']?\s*[:=]\s*[\"']?)([\w-]{11})")


def snapshot(channel: dict, videos: list[dict]) -> dict:
    sn = channel.get("snippet", {})
    return {"title": sn.get("title", ""), "custom_url": sn.get("customUrl", ""),
            "description_sha": hashlib.sha256(sn.get("description", "").encode("utf-8")).hexdigest(),
            "videos": {v["id"]: v.get("snippet", {}).get("title", "") for v in videos}}


def diff(base: dict, now: dict, known: set[str]) -> list[str]:
    out = []
    if now["title"] != base["title"]:
        out.append(f"Channel renamed: «{base['title']}» → «{now['title']}»")
    if now["custom_url"] != base["custom_url"]:
        out.append(f"Channel handle changed: {base['custom_url']} → {now['custom_url']}")
    if now["description_sha"] != base["description_sha"]:
        out.append("Channel description changed")
    for vid, title in now["videos"].items():
        if vid not in base["videos"] and vid not in known:
            out.append(f"Upload the pipeline did not make: «{title}» https://youtu.be/{vid}")
    for vid, title in base["videos"].items():
        if vid not in now["videos"]:
            out.append(f"Video gone (deleted or hidden): «{title}» https://youtu.be/{vid}")
    return out


def known_ids(root: Path = ROOT) -> set[str]:
    """Every YouTube video ID our own records mention: what the pipeline (or the founder, through it) published."""
    ids: set[str] = set()
    files = list((root / "data").glob("*.json")) + [p for p in (root / "reviewed").rglob("*")
                                                     if p.suffix in (".json", ".yaml", ".yml", ".txt")]
    for f in files:
        try:
            ids |= set(_YT_ID.findall(f.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError):
            continue
    return ids


def main() -> int:
    from scripts import channel as yt
    from scripts.notify import whatsapp
    tok = yt.token()
    vids = yt.videos(tok, limit=50)
    ch = vids[0]["channel"] if vids else yt.get("channels", tok, part="snippet", mine="true")["items"][0]
    now = snapshot(ch, vids)
    if not STATE.exists():
        STATE.write_text(json.dumps(now, ensure_ascii=False, indent=1), encoding="utf-8")
        print("Integrity: first snapshot saved")
        return 0
    alerts = diff(json.loads(STATE.read_text(encoding="utf-8")), now, known_ids())
    STATE.write_text(json.dumps(now, ensure_ascii=False, indent=1), encoding="utf-8")
    if not alerts:
        print("Integrity: no change")
        return 0
    body = "\n".join(f"- {a}" for a in alerts) + (
        "\n\nIf you did not make these changes: sign in to YouTube Studio now, remove unknown managers, "
        "sign out all other sessions in your Google account, and change the password. See docs/SECURITY.md.")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    n = yt.gh("issue", "list", "--repo", repo, "--state", "open", "--search", "Security: channel changed in:title",
              "--json", "number", "-q", ".[0].number").strip()
    if n:
        yt.gh("issue", "comment", n, "--repo", repo, "--body", body)
    else:
        yt.gh("issue", "create", "--repo", repo, "--title", "Security: channel changed", "--body", body)
    whatsapp("AI This Week security check: " + "; ".join(alerts)[:700])
    print("ALERT:", *alerts, sep="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
