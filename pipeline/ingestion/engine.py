"""Phase 1 entry point: RSS + X → scored, filtered, de-duplicated NewsItems."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.ingestion.rss_ingest import fetch_all_feeds
from pipeline.ingestion.scoring import rank_and_filter
from pipeline.ingestion.x_ingest import fetch_top_posts
from pipeline.models import NewsItem

log = logging.getLogger(__name__)


def run_ingestion(cfg: dict[str, Any]) -> list[NewsItem]:
    items = fetch_all_feeds(cfg)
    try:
        items += fetch_top_posts(cfg)
    except RuntimeError as exc:
        # Missing X token or exhausted quota: the episode can still be built from RSS.
        log.error("X ingestion skipped: %s", exc)

    ranked = rank_and_filter(items, cfg)
    if not ranked:
        raise RuntimeError("Ingestion produced no items above the relevance threshold — check feeds/keys.")
    return ranked
