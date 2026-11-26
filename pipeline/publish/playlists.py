"""Topic playlists, filled at upload (founder 2026-11-26: keep viewers watching the next video).

Every episode goes into the weekly-episodes playlist and every Short into the Shorts playlist; both also go into
each topic playlist whose words appear in the title or text (config publish.playlists). A playlist that does not
exist yet is created, public. Placing a video never fails an upload or a release: errors are logged and returned.
Quota: playlists.list 1 unit a page, playlists.insert and playlistItems.insert 50 each."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]


def rules(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    return list(cfg.get("publish", {}).get("playlists") or [])


def pick(title: str, text: str, kind: str, cfg: dict[str, Any]) -> list[str]:
    """Playlist titles for a video: those for its kind (episode or short) whose words appear in its title or the
    first paragraph of its text. Hashtags and the rest of a description (sources, links) are left out: the house
    hashtags carry #ChatGPT and an episode's source list names every company (2026-11-26 preview)."""
    lead = re.sub(r"#\w+", " ", (text or "").strip()).split("\n\n")[0]
    hay = f"{title}\n{lead}"
    out = []
    for r in rules(cfg):
        if kind not in (r.get("kinds") or ["episode", "short"]):
            continue
        words = r.get("match") or []
        if not words or any(re.search(rf"(?<![A-Za-z]){re.escape(w)}", hay, re.I) for w in words):
            out.append(r["title"])
    return out


def existing(yt) -> dict[str, str]:
    """The channel's playlists, title → id."""
    found, token = {}, None
    while True:
        res = yt.playlists().list(part="snippet", mine=True, maxResults=50, pageToken=token).execute()
        for p in res.get("items", []):
            found[p["snippet"]["title"]] = p["id"]
        token = res.get("nextPageToken")
        if not token:
            return found


def ensure(yt, titles: list[str], cfg: dict[str, Any], have: dict[str, str] | None = None) -> dict[str, str]:
    have = existing(yt) if have is None else have
    desc = {r["title"]: r.get("description", "") for r in rules(cfg)}
    for t in titles:
        if t not in have:
            res = yt.playlists().insert(part="snippet,status", body={
                "snippet": {"title": t, "description": desc.get(t, "")},
                "status": {"privacyStatus": "public"}}).execute()
            have[t] = res["id"]
            log.info("Playlist created: %s", t)
    return have


def in_playlist(yt, playlist_id: str, video_id: str) -> bool:
    """False also when YouTube does not know the playlist yet: a playlist created seconds ago answers 404 to
    playlistItems.list for a while (2026-11-26 backfill), while playlistItems.insert already works."""
    try:
        res = yt.playlistItems().list(part="id", playlistId=playlist_id, videoId=video_id, maxResults=1).execute()
    except Exception as exc:  # noqa: BLE001
        if "404" in str(exc):
            return False
        raise
    return bool(res.get("items"))


def place(yt, video_id: str, title: str, text: str, kind: str, cfg: dict[str, Any],
          have: dict[str, str] | None = None) -> list[str]:
    """Adds the video to its playlists; returns the titles it is now in (or an error line). Never raises."""
    titles = pick(title, text, kind, cfg)
    if not titles:
        return []
    try:
        have = ensure(yt, titles, cfg, have)
        for t in titles:
            if not in_playlist(yt, have[t], video_id):
                yt.playlistItems().insert(part="snippet", body={"snippet": {
                    "playlistId": have[t], "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
        return titles
    except Exception as exc:  # noqa: BLE001 — a playlist is a nicety; the video is already out
        log.warning("Playlists not updated for %s: %s", video_id, exc)
        return [f"error: {str(exc)[:200]}"]


def latest_episode_url(root: Path = ROOT) -> str:
    """The newest public episode on YouTube (data/releases.json), or ''."""
    f = root / "data" / "releases.json"
    rel = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    public = [r for r in rel if r.get("status") == "public" and r.get("video_id")]
    public.sort(key=lambda r: str(r.get("at") or r.get("release_at") or ""))
    return f"https://youtu.be/{public[-1]['video_id']}" if public else ""


def first_comment_text(cfg: dict[str, Any], previous_url: str = "") -> str:
    """The channel's own first comment on a new episode: a question for the comments, and the previous episode."""
    c = cfg.get("publish", {}).get("first_comment") or {}
    lines = [c.get("question", "Which of this week's stories matters most for your company? Tell us below.")]
    if previous_url:
        lines.append(f"{c.get('previous', 'Missed last week?')} {previous_url}")
    return "\n\n".join(lines)


def post_comment(yt, video_id: str, text: str) -> str:
    res = yt.commentThreads().insert(part="snippet", body={"snippet": {
        "videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}}).execute()
    return res.get("id", "")
