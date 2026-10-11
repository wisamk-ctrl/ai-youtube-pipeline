"""
Phase 5 — upload to YouTube (Data API v3).

Takes the final MP4 (captioned if Phase 4 ran, else the raw render), the Arabic
title from plan.json, and a description built from the editorial plan, and
uploads as *private* with a scheduled publish time. Private-then-scheduled
means a bad upload can still be caught before anyone sees it.

Compliance: `containsSyntheticMedia: true` sets YouTube's required
"altered or synthetic content" disclosure for a cloned face and voice.

Quota: an upload costs ~1,600 of the default 10,000 daily units — fine for
one episode a week. The API never bypasses YouTube's own processing time.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from googleapiclient.http import MediaFileUpload

log = logging.getLogger(__name__)

CATEGORY_SCIENCE_TECH = "28"


def build_description(plan: dict[str, Any], sources: list[dict[str, Any]], cfg: dict[str, Any]) -> str:
    """Arabic description: hook, chaptered story list, sources, disclosure, hashtags."""
    lines = [plan.get("cold_open_hook_en", "").strip(), ""]
    lines.append("في هذه الحلقة:")
    for seg in plan.get("segments", []):
        lines.append(f"• {seg['headline_en']}")
    lines += ["", "المصادر:"]
    seen = set()
    for s in sources:
        if s["url"] in seen or s["url"].startswith("mailto:"):
            continue
        seen.add(s["url"])
        lines.append(f"- {s['title']}: {s['url']}")
    lines += [
        "",
        "تنويه: يقدّم هذه الحلقة توأم رقمي للمقدّم مولّد بالذكاء الاصطناعي. المحتوى للمعلومات العامة فقط وليس نصيحة استثمارية أو قانونية.",
        "",
        " ".join(cfg["publish"].get("hashtags", [])),
    ]
    return "\n".join(lines)[:5000]  # YouTube's description limit


def next_publish_time(cfg: dict[str, Any]) -> datetime:
    """Next occurrence of the configured weekday/hour, in UTC."""
    p = cfg["publish"]
    now = datetime.now(timezone.utc)
    target = now.replace(hour=p["publish_hour_utc"], minute=0, second=0, microsecond=0)
    days_ahead = (p["publish_weekday"] - now.weekday()) % 7
    if days_ahead == 0 and target <= now:
        days_ahead = 7
    return target + timedelta(days=days_ahead)


def upload(video: Path, plan: dict[str, Any], sources: list[dict[str, Any]], cfg: dict[str, Any],
           thumbnail: Path | None = None, publish_at: datetime | None = None) -> str:
    from pipeline.google_auth import client  # lazy

    yt = client("youtube")
    publish_at = publish_at or next_publish_time(cfg)
    body = {
        "snippet": {
            "title": plan["episode_title_ar"][:100],
            "description": build_description(plan, sources, cfg),
            "tags": cfg["publish"].get("tags", [])[:30],
            "categoryId": CATEGORY_SCIENCE_TECH,
            "defaultLanguage": "ar",
            "defaultAudioLanguage": "ar",
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:  # resumable upload: loop until the final chunk is acknowledged
        status, response = request.next_chunk()
        if status:
            log.info("Upload %.0f%%", status.progress() * 100)
    video_id = response["id"]
    log.info("Uploaded https://youtu.be/%s — scheduled for %s", video_id, publish_at.isoformat())

    if thumbnail and thumbnail.exists():
        yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumbnail))).execute()
    return video_id


def run_publish(out_dir: Path, cfg: dict[str, Any]) -> str:
    video = next((p for p in (out_dir / "final_subtitled.mp4", out_dir / "talking_head.mp4") if p.exists()), None)
    if not video:
        raise FileNotFoundError("no rendered video in " + str(out_dir))
    plan = json.loads((out_dir / "plan.json").read_text(encoding="utf-8"))
    items = json.loads((out_dir / "items.json").read_text(encoding="utf-8"))
    used = {i for s in plan["segments"] for i in s["item_ids"]} | set(plan.get("quick_fire_item_ids", []))
    sources = [i for i in items if i["id"] in used]
    thumb = out_dir / "thumbnail.png"
    video_id = upload(video, plan, sources, cfg, thumbnail=thumb if thumb.exists() else None)
    (out_dir / "youtube.json").write_text(json.dumps({"video_id": video_id, "url": f"https://youtu.be/{video_id}"}), encoding="utf-8")
    return video_id
