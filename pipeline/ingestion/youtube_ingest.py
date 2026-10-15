"""
Phase 1d — YouTube channels as a news source.

Every channel has an Atom feed (no API key): youtube.com/feeds/videos.xml?channel_id=UC…
Channels are configured by handle; the handle is resolved to a channel id by reading the
channel page once and the result is cached in data/youtube_channels.json, so the weekly
run makes one HTML request per NEW handle and one feed request per channel.

A video is a lead, not a source: items carry source_type "youtube" and a weight < 1, so
the editor sees them but a written source on the same story outranks them.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import feedparser
import requests

from pipeline.config import ROOT
from pipeline.ingestion.rss_ingest import _entry_datetime
from pipeline.ingestion.text_utils import BROWSER_HEADERS, strip_html, truncate
from pipeline.models import NewsItem

log = logging.getLogger(__name__)

CACHE_PATH = ROOT / "data" / "youtube_channels.json"
FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
# Order matters: the page embeds OTHER channels' ids too (featured channels, recommendations), so the
# first "channelId" in the HTML is not always this channel. The canonical link and externalId are.
CHANNEL_ID_PATTERNS = (
    re.compile(r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[0-9A-Za-z_-]{22})"'),
    re.compile(r'"externalId":"(UC[0-9A-Za-z_-]{22})"'),
    re.compile(r'<meta itemprop="identifier" content="(UC[0-9A-Za-z_-]{22})"'),
    re.compile(r'"channelId":"(UC[0-9A-Za-z_-]{22})"'),
)
_HEADERS = BROWSER_HEADERS


def load_cache(path: Path = CACHE_PATH) -> dict[str, str]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache: dict[str, str], path: Path = CACHE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_handle(handle: str, timeout: int, session: requests.Session | None = None) -> str:
    """@handle → UC… channel id, from the channel page's embedded metadata."""
    handle = handle.lstrip("@")
    resp = (session or requests).get(f"https://www.youtube.com/@{handle}", headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    for pat in CHANNEL_ID_PATTERNS:
        m = pat.search(resp.text)
        if m:
            return m.group(1)
    raise ValueError(f"no channel id found on youtube.com/@{handle}")


def channel_id_for(ch: dict[str, Any], cache: dict[str, str], timeout: int) -> str:
    if ch.get("channel_id"):
        return ch["channel_id"]
    handle = ch["handle"].lstrip("@").lower()
    if handle not in cache:
        cache[handle] = resolve_handle(handle, timeout)
        log.info("YouTube @%s → %s (cached)", handle, cache[handle])
    return cache[handle]


def parse_feed(name: str, content: bytes, weight: float, since: datetime, max_items: int) -> list[NewsItem]:
    parsed = feedparser.parse(content)
    items: list[NewsItem] = []
    for entry in parsed.entries:
        published = _entry_datetime(entry)
        if published is None or published < since:
            continue
        body = entry.get("media_description") or entry.get("summary", "")
        items.append(NewsItem(
            source=name, source_type="youtube",
            title=strip_html(entry.get("title", "")),
            summary=truncate(strip_html(body), 1500),
            url=entry.get("link", ""), published=published,
            author=entry.get("author", name), source_weight=weight,
        ))
        if len(items) >= max_items:
            break
    return items


def fetch_feed_bytes(cid: str, timeout: int) -> bytes:
    """YouTube's feed endpoint answers 404 to some header sets; try browser headers, then none."""
    last: Exception | None = None
    for headers in (_HEADERS, {}):
        try:
            resp = requests.get(FEED_URL.format(cid=cid), headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.content
        except requests.HTTPError as exc:
            last = exc
            if exc.response is None or exc.response.status_code not in (403, 404):
                raise
    raise last  # type: ignore[misc]


API_URL = "https://www.googleapis.com/youtube/v3/playlistItems"


def fetch_uploads_api(cid: str, api_key: str, weight: float, since: datetime, max_items: int, name: str,
                      timeout: int) -> list[NewsItem]:
    """YouTube Data API v3: the channel's uploads playlist is 'UU' + the id without 'UC' (1 quota unit per call).
    Datacenter IPs (GitHub runners) get 404 from the Atom feed endpoint; the API answers from anywhere."""
    playlist = "UU" + cid[2:]
    resp = requests.get(API_URL, params={"part": "snippet", "playlistId": playlist, "maxResults": 15, "key": api_key},
                        timeout=timeout)
    resp.raise_for_status()
    items: list[NewsItem] = []
    for row in resp.json().get("items", []):
        sn = row.get("snippet", {})
        published = datetime.fromisoformat(sn.get("publishedAt", "").replace("Z", "+00:00")) if sn.get("publishedAt") else None
        if published is None or published < since:
            continue
        vid = sn.get("resourceId", {}).get("videoId", "")
        items.append(NewsItem(
            source=name, source_type="youtube", title=strip_html(sn.get("title", "")),
            summary=truncate(strip_html(sn.get("description", "")), 1500),
            url=f"https://www.youtube.com/watch?v={vid}", published=published,
            author=sn.get("channelTitle", name), source_weight=weight,
        ))
        if len(items) >= max_items:
            break
    return items


def fetch_youtube_channels(cfg: dict[str, Any]) -> list[NewsItem]:
    ing = cfg["ingestion"]
    yt = ing.get("youtube") or {}
    if not yt.get("enabled"):
        return []
    since = datetime.now(timezone.utc) - timedelta(days=ing["lookback_days"])
    timeout, per = ing["request_timeout_s"], int(yt.get("max_per_channel", 5))
    cache, out = load_cache(), []
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    log.info("YouTube via %s", "Data API" if api_key else "Atom feeds (set YOUTUBE_API_KEY on a datacenter runner)")
    for ch in yt.get("channels", []):
        try:
            cid = channel_id_for(ch, cache, timeout)
            if api_key:
                items = fetch_uploads_api(cid, api_key, float(ch.get("weight", 0.8)), since, per, ch["name"], timeout)
            else:
                items = parse_feed(ch["name"], fetch_feed_bytes(cid, timeout), float(ch.get("weight", 0.8)), since, per)
            log.info("YouTube %-20s %2d videos in window", ch["name"], len(items))
            out.extend(items)
        except Exception as exc:  # noqa: BLE001 — one channel must never kill the run
            log.error("YouTube channel %r failed: %s", ch.get("name"), exc)
    save_cache(cache)
    return out
