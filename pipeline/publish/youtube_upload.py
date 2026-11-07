"""
Phase 5 — upload to YouTube (Data API v3).

Takes the final MP4 (captioned if Phase 4 ran, else the raw render), the Arabic title from
plan.json and a description built by publish/description.py (Arabic hook, chapters on the final
video's times, sources, stock credits, disclosure), uploads it with the scheduled publish time,
then:
- thumbnail.png (phase post, post/packaging.py) via thumbnails().set
- the script-exact Arabic captions (subtitles.final.srt — shifted for the sting — else
  subtitles.srt) via captions().insert, language ar, name «العربية»
- English title/description through `localizations` when the plan has English fields
- the week's Shorts (shorts/shorts.json), each linking to the episode, only when
  publish.shorts.enabled is true (off until the founder turns it on)

Compliance: `containsSyntheticMedia: true` sets YouTube's required "altered or synthetic content"
disclosure for a cloned face and voice; the episode also shows it on screen (post overlays).

Scopes: videos.insert and thumbnails.set work with youtube.upload; captions.insert needs
youtube.force-ssl. A token without it gets a warning and the episode stays uploaded (re-run
scripts/google_authorize.py youtube with that scope added to upload captions).

Quota: an upload costs ~1,600 of the default 10,000 daily units, a caption track 400, a thumbnail
50; three Shorts add ~4,800 — still inside one day's quota.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pipeline.publish import description as desc

log = logging.getLogger(__name__)

CATEGORY_SCIENCE_TECH = "28"
CAPTION_NAMES = {"ar": "العربية", "en": "English"}


def build_description(plan: dict[str, Any], sources: list[dict[str, Any]], cfg: dict[str, Any], **kw: Any) -> str:
    """Kept for callers of the old name; see publish/description.py."""
    return desc.build_description(plan, sources, cfg, **kw)


def next_publish_time(cfg: dict[str, Any]) -> datetime:
    """Next occurrence of the configured weekday/hour, in UTC."""
    p = cfg["publish"]
    now = datetime.now(timezone.utc)
    target = now.replace(hour=p["publish_hour_utc"], minute=0, second=0, microsecond=0)
    days_ahead = (p["publish_weekday"] - now.weekday()) % 7
    if days_ahead == 0 and target <= now:
        days_ahead = 7
    return target + timedelta(days=days_ahead)


def _media(path: Path, mimetype: str | None = None, resumable: bool = False):
    from googleapiclient.http import MediaFileUpload
    if resumable:
        return MediaFileUpload(str(path), mimetype=mimetype, chunksize=8 * 1024 * 1024, resumable=True)
    return MediaFileUpload(str(path), mimetype=mimetype) if mimetype else MediaFileUpload(str(path))


def _status(cfg: dict[str, Any], publish_at: datetime) -> dict[str, Any]:
    return {
        "privacyStatus": cfg["publish"].get("privacy", "unlisted"),
        "publishAt": publish_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "selfDeclaredMadeForKids": False,
        "containsSyntheticMedia": True,
    }


def video_body(plan: dict[str, Any], description: str, cfg: dict[str, Any], publish_at: datetime,
               locs: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "snippet": {
            "title": desc.clean(plan["episode_title_ar"])[: desc.TITLE_LIMIT],
            "description": description,
            "tags": cfg["publish"].get("tags", [])[:30],
            "categoryId": CATEGORY_SCIENCE_TECH,
            "defaultLanguage": "ar",
            "defaultAudioLanguage": "ar",
        },
        "status": _status(cfg, publish_at),
    }
    if locs:
        body["localizations"] = locs
    return body


def _insert(yt, body: dict[str, Any], video: Path) -> str:
    part = ",".join(k for k in ("snippet", "status", "localizations") if k in body)
    request = yt.videos().insert(part=part, body=body, media_body=_media(video, "video/mp4", resumable=True))
    response = None
    while response is None:  # resumable upload: loop until the final chunk is acknowledged
        status, response = request.next_chunk()
        if status:
            log.info("Upload %.0f%%", status.progress() * 100)
    return response["id"]


def upload_captions(yt, video_id: str, srt: Path, language: str = "ar") -> str | None:
    """The caption track. Returns its id, or None when YouTube refused it (logged, not fatal)."""
    body = {"snippet": {"videoId": video_id, "language": language,
                        "name": CAPTION_NAMES.get(language, language), "isDraft": False}}
    try:
        res = yt.captions().insert(part="snippet", body=body,
                                   media_body=_media(srt, "application/octet-stream")).execute()
    except Exception as e:  # noqa: BLE001 — usually a token without youtube.force-ssl
        log.warning("Caption track not uploaded (%s). captions.insert needs the youtube.force-ssl scope.", e)
        return None
    log.info("Caption track %s uploaded (%s)", srt.name, language)
    return res.get("id")


def caption_file(out_dir: Path) -> Path | None:
    return next((p for p in (out_dir / "subtitles.final.srt", out_dir / "subtitles.srt") if p.exists()), None)


def thumbnail_file(out_dir: Path) -> Path | None:
    png, jpg = out_dir / "thumbnail.png", out_dir / "thumbnail.jpg"
    if png.exists() and png.stat().st_size <= 2 * 1024 * 1024:
        return png
    return jpg if jpg.exists() else (png if png.exists() else None)


def upload(video: Path, plan: dict[str, Any], sources: list[dict[str, Any]], cfg: dict[str, Any],
           thumbnail: Path | None = None, publish_at: datetime | None = None, description: str | None = None,
           captions: Path | None = None, language: str = "ar", yt=None) -> str:
    if yt is None:
        from pipeline.google_auth import client  # lazy
        yt = client("youtube")
    publish_at = publish_at or next_publish_time(cfg)
    text = description if description is not None else desc.build_description(plan, sources, cfg)
    locs = desc.localizations(plan, sources, cfg) if cfg["publish"].get("localizations", True) else {}
    video_id = _insert(yt, video_body(plan, text, cfg, publish_at, locs), video)
    log.info("Uploaded https://youtu.be/%s — scheduled for %s", video_id, publish_at.isoformat())
    if thumbnail and thumbnail.exists():
        try:
            yt.thumbnails().set(videoId=video_id, media_body=_media(thumbnail)).execute()
        except Exception as e:  # noqa: BLE001 — custom thumbnails need a verified channel
            log.warning("Thumbnail not set (%s); the channel may need phone verification", e)
    if captions and cfg["publish"].get("caption_track", True):
        upload_captions(yt, video_id, captions, language)
    return video_id


def short_description(short: dict[str, Any], episode_id: str, cfg: dict[str, Any]) -> str:
    t = int(short.get("episode_start") or 0)
    link = f"https://youtu.be/{episode_id}" + (f"?t={t}" if t else "")
    lines = [desc.clean(short["title"]), "", f"الحلقة الكاملة: {link}", "", desc.DISCLOSURE_AR, "",
             " ".join(["#Shorts", *cfg["publish"].get("hashtags", [])])]
    return "\n".join(lines)[: desc.DESC_LIMIT]


def upload_shorts(out_dir: Path, episode_id: str, cfg: dict[str, Any], publish_at: datetime, yt) -> list[dict[str, Any]]:
    """Each Short with its title + #Shorts and the full-episode link; off unless publish.shorts.enabled."""
    if not cfg["publish"].get("shorts", {}).get("enabled", False):
        return []
    meta = out_dir / "shorts" / "shorts.json"
    if not meta.exists():
        return []
    done = []
    for s in json.loads(meta.read_text(encoding="utf-8")):
        f = out_dir / "shorts" / s["file"]
        if not f.exists():
            continue
        title = f"{desc.clean(s['title'])[:90]} #Shorts"
        body = {"snippet": {"title": title, "description": short_description(s, episode_id, cfg),
                            "tags": cfg["publish"].get("tags", [])[:30], "categoryId": CATEGORY_SCIENCE_TECH,
                            "defaultLanguage": "ar", "defaultAudioLanguage": "ar"},
                "status": _status(cfg, publish_at)}
        vid = _insert(yt, body, f)
        log.info("Short uploaded https://youtu.be/%s (%s)", vid, s["file"])
        done.append({"file": s["file"], "video_id": vid, "url": f"https://youtu.be/{vid}"})
    return done


def _week_language(out_dir: Path) -> str:
    try:
        from pipeline.language import week_language
        return week_language(out_dir.name)
    except Exception:  # noqa: BLE001
        return "ar"


def run_publish(out_dir: Path, cfg: dict[str, Any], yt=None) -> str:
    video = next((p for p in (out_dir / "final_subtitled.mp4", out_dir / "talking_head.mp4") if p.exists()), None)
    if not video:
        raise FileNotFoundError("no rendered video in " + str(out_dir))
    plan = json.loads((out_dir / "plan.json").read_text(encoding="utf-8"))
    items = json.loads((out_dir / "items.json").read_text(encoding="utf-8"))
    sources = desc.pick_sources(out_dir, plan, items)
    sections, duration = desc.load_sections(out_dir, cfg)
    script = (out_dir / "script.md").read_text(encoding="utf-8") if (out_dir / "script.md").exists() else None
    cred = out_dir / "credits.json"
    credits = json.loads(cred.read_text(encoding="utf-8")) if cred.exists() else []
    text = desc.build_description(plan, sources, cfg, sections=sections, duration=duration, script=script, credits=credits)
    (out_dir / "description.txt").write_text(text, encoding="utf-8")   # what was sent, for review
    if yt is None:
        from pipeline.google_auth import client  # lazy
        yt = client("youtube")
    publish_at = next_publish_time(cfg)
    # The raw render has no sting, so its captions are the unshifted ones.
    raw_srt = out_dir / "subtitles.srt"
    captions = caption_file(out_dir) if video.name == "final_subtitled.mp4" else (raw_srt if raw_srt.exists() else None)
    video_id = upload(video, plan, sources, cfg, thumbnail=thumbnail_file(out_dir), publish_at=publish_at,
                      description=text, captions=captions, language=_week_language(out_dir), yt=yt)
    shorts = upload_shorts(out_dir, video_id, cfg, publish_at, yt)
    (out_dir / "youtube.json").write_text(json.dumps({"video_id": video_id, "url": f"https://youtu.be/{video_id}",
                                                      "shorts": shorts}, ensure_ascii=False), encoding="utf-8")
    return video_id
