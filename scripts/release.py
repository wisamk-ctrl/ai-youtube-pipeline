"""Make a gated episode public once YouTube has finished with it (founder 2026-11-18).

W46-en went public straight after upload, before YouTube had made its frame previews, and every chapter in
the chapter list showed the video's thumbnail. YouTube makes those chapter pictures itself and no API sets
them, so the only cure is time: upload unlisted, wait until each chapter shows its own picture, then publish.

2026-11-23: measured, those pictures arrive two to five days after publishing, on any channel (W46-en had none
after 1.5 days and all ten after five). No wait of hours can produce them, so `publish.chapter_wait_hours` is 0:
the episode goes public at its release time and this script is the scheduler. The check still runs and its
finding is kept in the note.

data/releases.json holds the waiting episodes: {week, video_id, release_at, status}. Every run (workflow
`release`, every 20 minutes) checks each waiting one:
  - chapters ready and release time reached → made public;
  - release time reached but chapters not ready → keeps waiting, up to `publish.chapter_wait_hours`
    (default 6) past the release time, then made public anyway and noted, so the news is never held for long.
Usage: python scripts/release.py          (check all)
       python scripts/release.py add <week> <video id> <release time ISO>"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
QUEUE = ROOT / "data" / "releases.json"
log = logging.getLogger("release")


def load() -> list[dict]:
    return json.loads(QUEUE.read_text(encoding="utf-8")) if QUEUE.exists() else []


def save(q: list[dict]) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE.write_text(json.dumps(q, indent=2), encoding="utf-8")


def add(week: str, video_id: str, release_at: datetime) -> None:
    q = [e for e in load() if e["video_id"] != video_id]
    q.append({"week": week, "video_id": video_id, "release_at": release_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
              "status": "waiting"})
    save(q)


def chapters_ready(video_id: str) -> tuple[bool | None, str]:
    """True when YouTube shows each chapter with its own picture (a video without chapters counts as ready).
    None when the page cannot be read at all: W47-en sat unlisted past its 17:00 slot because the runner met
    YouTube's sign-in wall on every check, so a check that cannot see releases on time and says so."""
    import hashlib
    import requests
    from scripts.youtube_video_check import UA, chapters
    html = requests.get(f"https://www.youtube.com/watch?v={video_id}", headers=UA, timeout=60).text
    if '"playabilityStatus":{"status":"LOGIN_REQUIRED"' in html:
        # YouTube's bot wall hides the frame previews from this runner: no verdict, so the time limit decides.
        return None, "YouTube sign-in wall on this runner: chapter pictures could not be checked"
    ch = chapters(html)
    if not ch:
        # No chapters on the page (none in the description, or not shown yet): fall back to the frame preview.
        story = "playerStoryboardSpecRenderer" in html
        return story, "frame previews " + ("present" if story else "not made yet")
    pics = {hashlib.md5(requests.get(c["picture"], headers=UA, timeout=60).content).hexdigest() for c in ch if c["picture"]}
    return len(pics) == len(ch), f"{len(pics)} pictures for {len(ch)} chapters"


def announce(week: str, video_id: str) -> None:
    """Now that it is public: post the episode on LinkedIn and the Facebook Page (weekly.yml phase announce)."""
    import os
    import subprocess
    if not os.environ.get("GITHUB_REPOSITORY"):
        return
    r = subprocess.run(["gh", "workflow", "run", "weekly.yml", "--repo", os.environ["GITHUB_REPOSITORY"], "--ref", "main",
                        "-f", "phase=announce", "-f", f"week={week}", "-f", f"video_url={video_id}"],
                       capture_output=True, text=True)
    log.info("announce %s: %s", week, "started" if r.returncode == 0 else r.stderr.strip()[:200])


def youtube():
    from pipeline.google_auth import client
    return client("youtube")


def run(now: datetime | None = None, ready=chapters_ready, make_public=None, wait_hours: float | None = None) -> list[str]:
    from pipeline.config import load_settings
    now = now or datetime.now(timezone.utc)
    if wait_hours is None:
        wait_hours = float(load_settings().get("publish", {}).get("chapter_wait_hours", 6))
    if make_public is None:
        def make_public(vid: str) -> None:
            yt = youtube()
            cur = yt.videos().list(part="status", id=vid).execute()["items"][0]["status"]
            cur["privacyStatus"] = "public"
            cur.pop("publishAt", None)
            yt.videos().update(part="status", body={"id": vid, "status": cur}).execute()
    q, lines = load(), []
    for e in q:
        if e.get("status") != "waiting":
            continue
        at = datetime.strptime(e["release_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        ok, why = ready(e["video_id"])
        late = now >= at + timedelta(hours=wait_hours)
        blind = ok is None
        if now >= at and (ok or blind or late):
            make_public(e["video_id"])
            e.update(status="public", at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                     note="chapters ready" if ok else f"released on time, {why}" if blind or not wait_hours
                     else f"made public after {wait_hours:g} h without chapter pictures ({why})")
            lines.append(f"✅ {e['week']} public: https://youtu.be/{e['video_id']} ({e['note']})")
            announce(e["week"], e["video_id"])
        else:
            e["last_check"] = f"{now:%Y-%m-%dT%H:%MZ}: {why}"
            lines.append(f"⏳ {e['week']} waiting: {why}; release {e['release_at']}")
    save(q)
    return lines


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) >= 5 and sys.argv[1] == "add":
        add(sys.argv[2], sys.argv[3], datetime.fromisoformat(sys.argv[4].replace("Z", "+00:00")))
    else:
        for line in run():
            print(line)
