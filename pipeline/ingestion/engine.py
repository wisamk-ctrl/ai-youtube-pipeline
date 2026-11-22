"""Phase 1 entry point: RSS + X → scored, filtered, de-duplicated NewsItems."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pipeline.ingestion.gmail_ingest import fetch_gmail_newsletters
from pipeline.ingestion.rss_ingest import fetch_all_feeds
from pipeline.ingestion.youtube_ingest import fetch_youtube_channels
from pipeline.ingestion.scoring import rank_and_filter
from pipeline.ingestion.watch_sources import fetch_watchlist_sources
from pipeline.ingestion.watchlist import load_watchlist
from pipeline.ingestion.x_ingest import fetch_top_posts
from pipeline.models import NewsItem

log = logging.getLogger(__name__)


def run_ingestion(cfg: dict[str, Any], week: str = "", out_dir: Path | None = None) -> list[NewsItem]:
    watch = load_watchlist()
    items = fetch_all_feeds(cfg)
    items += fetch_gmail_newsletters(cfg)
    items += fetch_youtube_channels(cfg)
    items += fetch_watchlist_sources(watch, cfg)
    try:
        items += fetch_top_posts(cfg)
    except RuntimeError as exc:
        # Missing X token or exhausted quota: the episode can still be built from RSS.
        log.error("X ingestion skipped: %s", exc)

    # What the six-hourly news watch kept this week: a story can leave the search results by Saturday.
    from pipeline.ingestion.news_watch import flagged_ids, kept_items
    have = {i.id for i in items}
    since = datetime.now(timezone.utc) - timedelta(days=cfg["ingestion"]["lookback_days"])
    items += [i for i in kept_items(since) if i.id not in have]
    flagged = flagged_ids(since)

    # Every item, whatever its source, is tagged with the watchlist names it mentions,
    # which sets its track (models / agents / chips) and region for the quotas and the plan.
    for item in items:
        watch.tag(item)
    # The radar looks for names that are NOT on the watchlist and adds the ones that clear
    # the bar as track="radar" items, so the editor can give them the رادار الأسبوع slot.
    from pipeline.radar.coverage import record, report_md
    from pipeline.radar.radar import run_radar
    wk = week or datetime.now(timezone.utc).strftime("%G-W%V")
    if out_dir:
        (out_dir / "coverage.md").write_text(report_md(record(items, watch, wk), watch, wk), encoding="utf-8")
    items += run_radar(items, watch, cfg, week or datetime.now(timezone.utc).strftime("%G-W%V"), out_dir)
    # Hype channels flagged lead_only have done their job (radar leads); they never reach the script.
    from pipeline.ingestion.youtube_ingest import is_lead_only
    items = [i for i in items if not is_lead_only(i, cfg)]
    from pipeline.ingestion import covered as cov
    done = cov.recent(cov.STATE, week or datetime.now(timezone.utc).strftime("%G-W%V"))
    ranked = rank_and_filter(items, cfg, flagged=flagged, covered=done)
    if not ranked:
        raise RuntimeError("Ingestion produced no items above the relevance threshold — check feeds/keys.")
    if out_dir:
        # The whole scored week, for the story ranking (pipeline/ranking clusters it; items.json keeps the top 30).
        import json
        (out_dir / "pool.json").write_text(json.dumps(
            [i.to_dict() for i in items if i.title.strip() and (i.score >= cfg["scoring"]["min_score"] or i.id in flagged)],
            ensure_ascii=False), encoding="utf-8")
        (out_dir / "flagged.json").write_text(json.dumps(sorted(flagged)), encoding="utf-8")
        from pipeline.ingestion.sources_report import sources_md
        (out_dir / "sources.md").write_text(sources_md(items, ranked), encoding="utf-8")
    return ranked
