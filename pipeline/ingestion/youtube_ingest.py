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
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import feedparser
import requests

from pipeline.config import ROOT
from pipeline.ingestion.rss_ingest import _entry_datetime
from pipeline.ingestion.text_utils import strip_html, truncate
from pipeline.models import NewsItem

log = logging.getLogger(__name__)

CACHE_PATH = ROOT / "data" / "youtube_channels.json"
FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
CHANNEL_ID_RE = re.compile(r'"(?:channelId|externalId)":"(UC[0-9A-Za-z_-]{22})"')
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ai-news-roundup/1.0)", "Accept-Language": "en"}


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
    m = CHANNEL_ID_RE.search(resp.text)
    if not m:
        raise ValueError(f"no channel id found on youtube.com/@{handle}")
    return m.group(1)


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


def fetch_youtube_channels(cfg: dict[str, Any]) -> list[NewsItem]:
    ing = cfg["ingestion"]
    yt = ing.get("youtube") or {}
    if not yt.get("enabled"):
        return []
    since = datetime.now(timezone.utc) - timedelta(days=ing["lookback_days"])
    timeout, per = ing["request_timeout_s"], int(yt.get("max_per_channel", 5))
    cache, out = load_cache(), []
    for ch in yt.get("channels", []):
        try:
            cid = channel_id_for(ch, cache, timeout)
            resp = requests.get(FEED_URL.format(cid=cid), headers=_HEADERS, timeout=timeout)
            resp.raise_for_status()
            items = parse_feed(ch["name"], resp.content, float(ch.get("weight", 0.8)), since, per)
            log.info("YouTube %-20s %2d videos in window", ch["name"], len(items))
            out.extend(items)
        except Exception as exc:  # noqa: BLE001 — one channel must never kill the run
            log.error("YouTube channel %r failed: %s", ch.get("name"), exc)
    save_cache(cache)
    return out
