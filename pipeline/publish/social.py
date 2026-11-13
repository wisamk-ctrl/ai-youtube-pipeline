"""
Short-form posting on the platforms' own APIs, no third-party service (founder 2026-11-13).

    YouTube Shorts   YouTube Data API (pipeline/google_auth.py)           posts public/unlisted at once
    Instagram Reels  Instagram API with Instagram Login (graph.instagram.com): container → publish
    TikTok           Content Posting API (open.tiktokapis.com), FILE_UPLOAD; an app TikTok has not
                     audited may only post SELF_ONLY (private), which the founder flips to public

None of the three schedules ahead through its API, so the pipeline keeps its own schedule:
data/social_queue.json, one entry per clip with a due time, an approval flag and each platform's
result. `plan_week` adds a week's clips (their files go to a public GitHub release, which also gives
Instagram the public URL it fetches from); `post_due` posts every approved entry whose time has come,
platform by platform, and records what happened, so a failed platform is retried on the next run
without posting twice on the others.

Tokens live in GitHub secrets. TikTok's access token lasts a day and Instagram's sixty, so each run
refreshes them and, with SECRETS_PAT set (a token allowed to write this repo's secrets), stores the
new ones back (`store_secret`).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import requests

log = logging.getLogger(__name__)

PLATFORMS = ("youtube", "instagram", "tiktok")
IG = "https://graph.instagram.com"
TT = "https://open.tiktokapis.com"


# ── Secrets ──────────────────────────────────────────────────────────────────
def store_secret(name: str, value: str) -> bool:
    """Write a repository secret with the gh CLI (needs SECRETS_PAT and GITHUB_REPOSITORY in CI)."""
    pat, repo = os.environ.get("SECRETS_PAT"), os.environ.get("GITHUB_REPOSITORY")
    if not (pat and repo and value):
        log.warning("Cannot store %s: SECRETS_PAT or GITHUB_REPOSITORY missing", name)
        return False
    r = subprocess.run(["gh", "secret", "set", name, "--repo", repo, "--body", value],
                       env={**os.environ, "GH_TOKEN": pat}, capture_output=True, text=True)
    if r.returncode != 0:
        log.warning("Storing %s failed: %s", name, r.stderr.strip()[-300:])
        return False
    log.info("Secret %s updated", name)
    return True


# ── The queue ────────────────────────────────────────────────────────────────
def load_queue(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def save_queue(path: Path, queue: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def due_times(first: datetime, count: int, days: list[int], hour_utc: int) -> list[datetime]:
    """`count` slots on the given weekdays (0 = Monday) at hour_utc, the first after `first`."""
    out, d = [], first.replace(minute=0, second=0, microsecond=0)
    d = d.replace(hour=hour_utc)
    if d <= first:
        d += timedelta(days=1)
    while len(out) < count:
        if d.weekday() in days:
            out.append(d)
        d += timedelta(days=1)
    return out


def caption(short: dict[str, Any], cfg: dict[str, Any], lang: str, platform: str) -> str:
    from pipeline.publish import description as desc
    s = cfg.get("social", {})
    tags = s.get(f"hashtags_{lang}") or cfg["publish"].get("hashtags_en" if lang == "en" else "hashtags", [])
    if platform == "youtube":
        tags = ["#Shorts", *tags]
    more = s.get(f"more_{lang}", "Full episode on YouTube: link in bio" if lang == "en" else "الحلقة الكاملة على يوتيوب")
    note = desc.DISCLOSURE_EN if lang == "en" else desc.DISCLOSURE_AR
    return "\n\n".join(x for x in (desc.clean(short.get("title", "")), more, note, " ".join(tags)) if x)


def plan_week(out_dir: Path, cfg: dict[str, Any], queue: list[dict[str, Any]], asset_url: Callable[[str], str],
              start: datetime | None = None) -> list[dict[str, Any]]:
    """Queue a week's vertical clips (shorts/shorts.json); returns the new entries. A week already queued is
    left alone, so a re-run of the edit never posts its clips twice."""
    from pipeline.language import week_language
    week, lang = out_dir.name, week_language(out_dir.name)
    if any(e["week"] == week for e in queue):
        log.info("Social: %s already queued", week)
        return []
    meta = out_dir / "shorts" / "shorts.json"
    shorts = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else []
    s = cfg.get("social", {})
    slots = due_times(start or datetime.now(timezone.utc), len(shorts), list(s.get("days", [0, 2, 4])),
                      int(s.get("hour_utc", 15)))
    platforms = [p for p in s.get("platforms", PLATFORMS) if p in PLATFORMS]
    new = []
    for n, (sh, due) in enumerate(zip(shorts, slots), 1):
        name = f"{week}-short-{n:02d}.mp4"
        new.append({
            "id": f"{week}#{n}", "week": week, "lang": lang, "file": name, "url": asset_url(name),
            "title": sh.get("title", ""), "due": due.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "approved": not s.get("require_approval", True),
            "captions": {p: caption(sh, cfg, lang, p) for p in platforms},
            "posts": {p: {"status": "queued"} for p in platforms},
        })
    queue.extend(new)
    return new


# ── Instagram ────────────────────────────────────────────────────────────────
class Instagram:
    def __init__(self, token: str, version: str = "v23.0", http=requests, sleep=time.sleep):
        self.token, self.v, self.http, self.sleep = token, version, http, sleep

    def _get(self, path: str, **params) -> dict[str, Any]:
        r = self.http.get(f"{IG}/{self.v}/{path}", params={**params, "access_token": self.token}, timeout=60)
        return _ok(r, "Instagram")

    def _post(self, path: str, **params) -> dict[str, Any]:
        r = self.http.post(f"{IG}/{self.v}/{path}", data={**params, "access_token": self.token}, timeout=120)
        return _ok(r, "Instagram")

    def user_id(self) -> str:
        return str(self._get("me", fields="user_id,username")["user_id"])

    def post_reel(self, video_url: str, text: str, wait_s: int = 600) -> str:
        """A Reel from a public video URL: create the container, wait until Instagram has fetched and processed
        it, publish. Returns the media id."""
        uid = self.user_id()
        cid = self._post(f"{uid}/media", media_type="REELS", video_url=video_url, caption=text,
                         share_to_feed="true")["id"]
        waited = 0
        while True:
            st = self._get(str(cid), fields="status_code,status").get("status_code")
            if st == "FINISHED":
                break
            if st in ("ERROR", "EXPIRED") or waited >= wait_s:
                raise RuntimeError(f"Instagram container {cid}: {st} after {waited} s")
            self.sleep(15)
            waited += 15
        return str(self._post(f"{uid}/media_publish", creation_id=cid)["id"])

    @staticmethod
    def refresh(token: str, http=requests) -> str:
        """A long-lived token (60 days) for a fresh one; refreshable once it is a day old."""
        r = http.get(f"{IG}/refresh_access_token", params={"grant_type": "ig_refresh_token", "access_token": token},
                     timeout=60)
        return str(_ok(r, "Instagram refresh")["access_token"])


# ── TikTok ───────────────────────────────────────────────────────────────────
class TikTok:
    CHUNK = 10 * 1024 * 1024

    def __init__(self, token: str, http=requests, sleep=time.sleep):
        self.token, self.http, self.sleep = token, http, sleep

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        r = self.http.post(f"{TT}{path}", json=body, timeout=60,
                           headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json; charset=UTF-8"})
        data = _ok(r, "TikTok")
        err = data.get("error", {})
        if err.get("code") not in (None, "ok"):
            raise RuntimeError(f"TikTok {path}: {err.get('code')}: {err.get('message')}")
        return data.get("data", {})

    def privacy(self, wanted: str) -> str:
        """The wanted privacy if the account offers it, else the most public it does (an unaudited app gets
        SELF_ONLY only)."""
        opts = self._post("/v2/post/publish/creator_info/query/", {}).get("privacy_level_options", [])
        for p in (wanted, "PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "FOLLOWER_OF_CREATOR", "SELF_ONLY"):
            if p in opts:
                return p
        return "SELF_ONLY"

    def post_video(self, path: Path, text: str, wanted: str = "PUBLIC_TO_EVERYONE", wait_s: int = 600) -> dict[str, Any]:
        size = path.stat().st_size
        chunk = size if size <= self.CHUNK else self.CHUNK
        count = max(1, size // chunk)               # TikTok: the last chunk takes the remainder
        level = self.privacy(wanted)
        init = self._post("/v2/post/publish/video/init/", {
            "post_info": {"title": text[:2200], "privacy_level": level, "is_aigc": True,
                          "disable_comment": False, "disable_duet": False, "disable_stitch": False},
            "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk,
                            "total_chunk_count": count}})
        with open(path, "rb") as f:
            for i in range(count):
                start = i * chunk
                end = size - 1 if i == count - 1 else start + chunk - 1
                f.seek(start)
                body = f.read(end - start + 1)
                r = self.http.put(init["upload_url"], data=body, timeout=300, headers={
                    "Content-Type": "video/mp4", "Content-Length": str(len(body)),
                    "Content-Range": f"bytes {start}-{end}/{size}"})
                if r.status_code not in (200, 201, 206):
                    raise RuntimeError(f"TikTok upload chunk {i + 1}/{count}: HTTP {r.status_code} {r.text[:200]}")
        waited = 0
        while True:
            st = self._post("/v2/post/publish/status/fetch/", {"publish_id": init["publish_id"]})
            status = st.get("status")
            if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
                return {"publish_id": init["publish_id"], "privacy": level, "status": status}
            if status == "FAILED" or waited >= wait_s:
                raise RuntimeError(f"TikTok publish {init['publish_id']}: {status} {st.get('fail_reason', '')}")
            self.sleep(10)
            waited += 10

    @staticmethod
    def refresh(client_key: str, client_secret: str, refresh_token: str, http=requests) -> dict[str, Any]:
        r = http.post(f"{TT}/v2/oauth/token/", timeout=60, headers={"Content-Type": "application/x-www-form-urlencoded"},
                      data={"client_key": client_key, "client_secret": client_secret,
                            "grant_type": "refresh_token", "refresh_token": refresh_token})
        data = _ok(r, "TikTok refresh")
        if "access_token" not in data:
            raise RuntimeError(f"TikTok refresh: {data.get('error')}: {data.get('error_description')}")
        return data


def _ok(r, who: str) -> dict[str, Any]:
    try:
        data = r.json()
    except ValueError:
        data = {}
    if r.status_code >= 400:
        err = data.get("error")
        msg = err.get("message") if isinstance(err, dict) else (data.get("error_description") or err or r.text[:300])
        raise RuntimeError(f"{who}: HTTP {r.status_code}: {msg}")
    return data


# ── Posting ──────────────────────────────────────────────────────────────────
def post_due(queue: list[dict[str, Any]], cfg: dict[str, Any], fetch: Callable[[dict[str, Any]], Path],
             posters: dict[str, Callable[[dict[str, Any], Path], dict[str, Any]]],
             now: datetime | None = None, only: str | None = None) -> list[str]:
    """Post every approved, due entry on each platform not yet done. Returns one line per attempt."""
    now = now or datetime.now(timezone.utc)
    lines = []
    for e in queue:
        if only and e["id"] != only:
            continue
        if not e.get("approved") or datetime.strptime(e["due"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) > now:
            continue
        todo = [p for p, r in e["posts"].items() if r.get("status") not in ("posted", "skipped") and p in posters]
        if not todo:
            continue
        local = fetch(e)
        for p in todo:
            r = e["posts"][p]
            r["attempts"] = int(r.get("attempts", 0)) + 1
            try:
                res = posters[p](e, local)
                r.update(status="posted", at=now.strftime("%Y-%m-%dT%H:%M:%SZ"), **res)
                r.pop("error", None)
                lines.append(f"✅ {e['id']} {p}: {res}")
            except Exception as exc:  # noqa: BLE001 — one platform failing must not stop the others
                r.update(status="failed", error=str(exc)[:500])
                if r["attempts"] >= int(cfg.get("social", {}).get("max_attempts", 3)):
                    r["status"] = "skipped"
                lines.append(f"❌ {e['id']} {p}: {exc}")
    return lines


def youtube_poster(cfg: dict[str, Any]):
    from pipeline.google_auth import client
    from pipeline.publish import youtube_upload as yu
    yt = client("youtube")

    def post(e: dict[str, Any], local: Path) -> dict[str, Any]:
        title = (e.get("title") or e["file"])[:90] + " #Shorts"
        body = {"snippet": {"title": title, "description": e["captions"]["youtube"],
                            "tags": cfg["publish"].get("tags_en" if e["lang"] == "en" else "tags", [])[:30],
                            "categoryId": yu.CATEGORY_SCIENCE_TECH, "defaultLanguage": e["lang"],
                            "defaultAudioLanguage": e["lang"]},
                "status": {"privacyStatus": cfg.get("social", {}).get("youtube_privacy", "public"),
                           "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
        vid = yu._insert(yt, body, local)
        return {"url": f"https://youtube.com/shorts/{vid}"}
    return post


def instagram_poster(cfg: dict[str, Any]):
    token = os.environ["INSTAGRAM_TOKEN"]
    try:   # keep the 60-day token alive: refresh every run, store the new one if we can
        new = Instagram.refresh(token)
        if new and new != token:
            store_secret("INSTAGRAM_TOKEN", new)
            token = new
    except Exception as exc:  # noqa: BLE001 — a fresh token (under a day old) cannot be refreshed yet
        log.info("Instagram token not refreshed: %s", exc)
    ig = Instagram(token, cfg.get("social", {}).get("instagram_api_version", "v23.0"))

    def post(e: dict[str, Any], _local: Path) -> dict[str, Any]:
        return {"media_id": ig.post_reel(e["url"], e["captions"]["instagram"])}
    return post


def tiktok_poster(cfg: dict[str, Any]):
    data = TikTok.refresh(os.environ["TIKTOK_CLIENT_KEY"], os.environ["TIKTOK_CLIENT_SECRET"],
                          os.environ["TIKTOK_REFRESH_TOKEN"])
    if data.get("refresh_token") and data["refresh_token"] != os.environ["TIKTOK_REFRESH_TOKEN"]:
        store_secret("TIKTOK_REFRESH_TOKEN", data["refresh_token"])
    tt = TikTok(data["access_token"])
    wanted = cfg.get("social", {}).get("tiktok_privacy", "PUBLIC_TO_EVERYONE")

    def post(e: dict[str, Any], local: Path) -> dict[str, Any]:
        return tt.post_video(local, e["captions"]["tiktok"], wanted)
    return post


def posters(cfg: dict[str, Any]) -> dict[str, Callable]:
    """The platforms whose secrets are present (a platform not yet connected is simply not posted to)."""
    need = {"youtube": ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"),
            "instagram": ("INSTAGRAM_TOKEN",),
            "tiktok": ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN")}
    make = {"youtube": youtube_poster, "instagram": instagram_poster, "tiktok": tiktok_poster}
    out = {}
    for p in cfg.get("social", {}).get("platforms", PLATFORMS):
        if all(os.environ.get(k) for k in need[p]):
            try:
                out[p] = make[p](cfg)
            except Exception as exc:  # noqa: BLE001 — a broken token on one platform must not stop the others
                log.warning("%s not available this run: %s", p, exc)
        else:
            log.info("%s not connected (secrets missing): skipped", p)
    return out
