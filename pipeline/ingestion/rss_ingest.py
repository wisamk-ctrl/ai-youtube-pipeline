"""
Phase 1a — RSS aggregation.

Fetches each configured newsletter feed, keeps entries published inside the
look-back window, and normalises them into NewsItem objects.

Design notes
------------
* We download with `requests` (which has a timeout) and hand the bytes to
  feedparser. feedparser's own URL fetching has no timeout, and one hung feed
  would stall the whole weekly run.
* One broken feed must never kill the run: each feed is isolated in its own
  try/except and logged. Losing one source is acceptable; losing the episode is not.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from time import mktime
from typing import Any

import feedparser
import requests

from pipeline.ingestion.text_utils import BROWSER_HEADERS, strip_html, truncate
from pipeline.models import NewsItem

log = logging.getLogger(__name__)

_HEADERS = BROWSER_HEADERS


def _entry_datetime(entry: Any) -> datetime | None:
    """Best-effort publication time. feedparser exposes parsed struct_time fields."""
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        st = entry.get(key)
        if st:
            return datetime.fromtimestamp(mktime(st), tz=timezone.utc)
    return None


def fetch_feed(name: str, url: str, weight: float, since: datetime, timeout: int) -> list[NewsItem]:
    """Fetch one feed and return its in-window entries as NewsItems."""
    resp = requests.get(url, headers=_HEADERS, timeout=timeout)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)

    if parsed.bozo and not parsed.entries:
        # bozo = malformed XML. feedparser still recovers entries most of the
        # time; only treat it as fatal when nothing at all was recovered.
        raise ValueError(f"unparseable feed: {parsed.bozo_exception!r}")

    items: list[NewsItem] = []
    for entry in parsed.entries:
        published = _entry_datetime(entry)
        if published is None or published < since:
            continue  # undated entries are skipped: we cannot prove they are this week's news

        # Prefer full content over the summary when the feed provides it.
        body = ""
        if entry.get("content"):
            body = entry["content"][0].get("value", "")
        body = body or entry.get("summary", "")

        items.append(
            NewsItem(
                source=name,
                source_type="rss",
                title=strip_html(entry.get("title", "")),
                # Cap the body: newsletters can be 5k+ words and we only need
                # enough for scoring and for the LLM to understand the story.
                summary=truncate(strip_html(body), 2500),
                url=entry.get("link", url),
                published=published,
                author=entry.get("author", ""),
                source_weight=weight,
            )
        )
    return items


def fetch_all_feeds(cfg: dict[str, Any]) -> list[NewsItem]:
    """Aggregate every configured feed, tolerating individual failures."""
    ing = cfg["ingestion"]
    since = datetime.now(timezone.utc) - timedelta(days=ing["lookback_days"])
    out: list[NewsItem] = []

    for feed in ing["rss_feeds"]:
        if not feed.get("url"):
            log.warning("RSS feed %r has no URL configured — skipped", feed["name"])
            continue
        try:
            items = fetch_feed(feed["name"], feed["url"], feed.get("weight", 1.0), since, ing["request_timeout_s"])
            log.info("RSS %-28s %3d items in window", feed["name"], len(items))
            out.extend(items)
        except Exception as exc:  # noqa: BLE001 — isolate every feed
            log.error("RSS feed %r failed: %s", feed["name"], exc)
    return out
