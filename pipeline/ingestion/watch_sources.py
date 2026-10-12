"""
Phase 1e — sources driven by the watchlist. All free, no keys required.

  Google News RSS   one search feed per entity ("<name>" when:7d) — the world's press on each name
  Official RSS      the entity's own blog / newsroom feeds listed in the watchlist
  GitHub releases   new tagged releases of the repos we follow (agents, open models)
  Hugging Face      new or updated models in the organisations we follow

Each source is isolated: a failure logs and moves on. Google News links are redirect
URLs, which is fine: the scorer de-duplicates on title similarity as well as URL.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from urllib.parse import quote_plus

import requests

from pipeline.ingestion.rss_ingest import fetch_feed
from pipeline.ingestion.text_utils import strip_html, truncate
from pipeline.ingestion.watchlist import Entity, Watchlist
from pipeline.models import NewsItem

log = logging.getLogger(__name__)
UA = {"User-Agent": "Mozilla/5.0 (compatible; ai-news-roundup/1.0)"}


def _since(cfg: dict[str, Any]) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=cfg["ingestion"]["lookback_days"])


# ── Google News ───────────────────────────────────────────────────────────────
def google_news_url(query: str, days: int, lang: str = "en", country: str = "US") -> str:
    # `when:Nd` keeps the window server-side; AI narrows "Arm"/"Apple" to the right stories.
    q = f"{query} AI when:{days}d"
    return f"https://news.google.com/rss/search?q={quote_plus(q)}&hl={lang}&gl={country}&ceid={country}:{lang}"


def fetch_google_news(watch: Watchlist, cfg: dict[str, Any], entities: Iterable[Entity] | None = None) -> list[NewsItem]:
    ing = cfg["ingestion"]
    days = ing["lookback_days"]
    out: list[NewsItem] = []
    for e in entities or watch.entities:
        url = google_news_url(e.news_query, days)
        try:
            items = fetch_feed(f"Google News · {e.name}", url, 0.9, _since(cfg), ing["request_timeout_s"])
        except Exception as exc:  # noqa: BLE001
            log.warning("Google News for %s failed: %s", e.name, exc)
            continue
        for i in items[: ing["watchlist"].get("max_per_entity", 8)]:
            # Google News titles end with " - Publisher"; keep the publisher as the source.
            title, _, publisher = i.title.rpartition(" - ")
            if publisher and title:
                i.title, i.source = title.strip(), publisher.strip()
            i.track, i.region, i.entities = e.track, e.group, [e.name]
            out.append(i)
    log.info("Google News: %d items across %d names", len(out), len(list(entities or watch.entities)))
    return out


# ── Official feeds ────────────────────────────────────────────────────────────
def fetch_official_feeds(watch: Watchlist, cfg: dict[str, Any]) -> list[NewsItem]:
    ing = cfg["ingestion"]
    out: list[NewsItem] = []
    for e in watch.entities:
        for url in e.rss:
            try:
                items = fetch_feed(e.name, url, 1.2, _since(cfg), ing["request_timeout_s"])  # first-party: high trust
            except Exception as exc:  # noqa: BLE001
                log.warning("Official feed %s (%s) failed: %s", e.name, url, exc)
                continue
            for i in items:
                i.track, i.region, i.entities = e.track, e.group, [e.name]
            out.extend(items)
    return out


# ── GitHub releases ───────────────────────────────────────────────────────────
def fetch_github_releases(watch: Watchlist, cfg: dict[str, Any]) -> list[NewsItem]:
    ing = cfg["ingestion"]
    headers = dict(UA, Accept="application/vnd.github+json")
    if os.environ.get("GITHUB_TOKEN"):  # optional: lifts the 60 req/h anonymous limit
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    since = _since(cfg)
    out: list[NewsItem] = []
    for e in (x for x in watch.entities if x.github):
        try:
            r = requests.get(f"https://api.github.com/repos/{e.github}/releases", params={"per_page": 5},
                             headers=headers, timeout=ing["request_timeout_s"])
            r.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning("GitHub releases %s failed: %s", e.github, exc)
            continue
        for rel in r.json():
            if rel.get("draft") or rel.get("prerelease"):
                continue
            published = datetime.fromisoformat(rel["published_at"].replace("Z", "+00:00"))
            if published < since:
                continue
            out.append(NewsItem(
                source=f"GitHub · {e.github}", source_type="rss",
                title=f"{e.name} releases {rel.get('name') or rel.get('tag_name')}",
                summary=truncate(strip_html(rel.get("body") or ""), 2000) or f"New release {rel.get('tag_name')} of {e.github}.",
                url=rel["html_url"], published=published, source_weight=1.1,
                track=e.track, region=e.group, entities=[e.name],
            ))
    log.info("GitHub releases: %d in window", len(out))
    return out


# ── Hugging Face ──────────────────────────────────────────────────────────────
def fetch_hf_models(watch: Watchlist, cfg: dict[str, Any]) -> list[NewsItem]:
    ing = cfg["ingestion"]
    since = _since(cfg)
    out: list[NewsItem] = []
    for e in (x for x in watch.entities if x.hf):
        try:
            r = requests.get("https://huggingface.co/api/models",
                             params={"author": e.hf, "sort": "createdAt", "direction": -1, "limit": 10},
                             headers=UA, timeout=ing["request_timeout_s"])
            r.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.warning("Hugging Face %s failed: %s", e.hf, exc)
            continue
        for m in r.json():
            created = datetime.fromisoformat(m.get("createdAt", "").replace("Z", "+00:00")) if m.get("createdAt") else None
            if not created or created < since:
                continue
            model_id = m["id"]
            out.append(NewsItem(
                source="Hugging Face", source_type="rss",
                title=f"{e.name} publishes {model_id.split('/')[-1]} on Hugging Face",
                summary=f"New model {model_id} ({m.get('pipeline_tag') or 'unspecified task'}), "
                        f"{m.get('downloads', 0):,} downloads and {m.get('likes', 0)} likes so far. "
                        f"Tags: {', '.join((m.get('tags') or [])[:8])}.",
                url=f"https://huggingface.co/{model_id}", published=created,
                engagement=int(m.get("likes", 0)), source_weight=1.0,
                track=e.track, region=e.group, entities=[e.name],
            ))
    log.info("Hugging Face: %d new models in window", len(out))
    return out


def fetch_watchlist_sources(watch: Watchlist, cfg: dict[str, Any]) -> list[NewsItem]:
    w = cfg["ingestion"].get("watchlist", {})
    if not w.get("enabled", True):
        return []
    out: list[NewsItem] = []
    if w.get("google_news", True):
        out += fetch_google_news(watch, cfg)
    if w.get("official_feeds", True):
        out += fetch_official_feeds(watch, cfg)
    if w.get("github", True):
        out += fetch_github_releases(watch, cfg)
    if w.get("huggingface", True):
        out += fetch_hf_models(watch, cfg)
    return out
