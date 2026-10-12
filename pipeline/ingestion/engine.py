"""Phase 1 entry point: RSS + X → scored, filtered, de-duplicated NewsItems."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.ingestion.gmail_ingest import fetch_gmail_newsletters
from pipeline.ingestion.rss_ingest import fetch_all_feeds
from pipeline.ingestion.scoring import rank_and_filter
from pipeline.ingestion.watch_sources import fetch_watchlist_sources
from pipeline.ingestion.watchlist import load_watchlist
from pipeline.ingestion.x_ingest import fetch_top_posts
from pipeline.models import NewsItem

log = logging.getLogger(__name__)


def run_ingestion(cfg: dict[str, Any]) -> list[NewsItem]:
    watch = load_watchlist()
    items = fetch_all_feeds(cfg)
    items += fetch_gmail_newsletters(cfg)
    items += fetch_watchlist_sources(watch, cfg)
    try:
        items += fetch_top_posts(cfg)
    except RuntimeError as exc:
        # Missing X token or exhausted quota: the episode can still be built from RSS.
        log.error("X ingestion skipped: %s", exc)

    # Every item, whatever its source, is tagged with the watchlist names it mentions,
    # which sets its track (models / agents / chips) and region for the quotas and the plan.
    for item in items:
        watch.tag(item)
    ranked = rank_and_filter(items, cfg)
    if not ranked:
        raise RuntimeError("Ingestion produced no items above the relevance threshold — check feeds/keys.")
    return ranked
