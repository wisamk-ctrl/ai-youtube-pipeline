"""Ingestion tests against realistic feed/API shapes, with HTTP mocked out."""

from __future__ import annotations

import base64
import json
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingestion import rss_ingest, x_ingest  # noqa: E402
from pipeline.ingestion.gmail_ingest import email_to_items, split_stories  # noqa: E402
from pipeline.ingestion.scoring import rank_and_filter  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
NOW = datetime.now(timezone.utc)
RECENT = NOW - timedelta(days=2)
OLD = NOW - timedelta(days=40)
CFG = {
    "ingestion": {"lookback_days": 7, "request_timeout_s": 5,
                  "rss_feeds": [{"name": "TLDR AI", "url": "https://tldr.tech/api/rss/ai", "weight": 1.2}],
                  "x": {"enabled": True, "top_n": 10, "max_posts_per_account": 100, "accounts": ["emollick"]}},
    "scoring": {"min_score": 2.0, "max_items": 25, "dedupe_similarity": 0.82},
}


def _rss_bytes() -> bytes:
    xml = (FIX / "tldr_ai_sample.xml").read_text(encoding="utf-8")
    return xml.replace("__RECENT__", format_datetime(RECENT)).replace("__OLD__", format_datetime(OLD)).encode()


def test_rss_feed_parses_window_and_prefers_full_content():
    resp = MagicMock(content=_rss_bytes(), raise_for_status=lambda: None)
    with patch.object(rss_ingest.requests, "get", return_value=resp):
        items = rss_ingest.fetch_feed("TLDR AI", "https://tldr.tech/api/rss/ai", 1.2, NOW - timedelta(days=7), 5)
    titles = [i.title for i in items]
    assert len(items) == 3 and "Old story from last month (5 minute read)" not in titles
    anthropic = next(i for i in items if "Anthropic" in i.title)
    assert anthropic.summary.startswith("Anthropic announced a 40%")  # content:encoded, not description
    assert all(i.source_weight == 1.2 for i in items)


def test_rss_then_scoring_drops_lifestyle_noise():
    resp = MagicMock(content=_rss_bytes(), raise_for_status=lambda: None)
    with patch.object(rss_ingest.requests, "get", return_value=resp):
        items = rss_ingest.fetch_all_feeds(CFG)
    kept = rank_and_filter(items, CFG)
    assert [i.title.split(" (")[0] for i in kept][:2] == [
        "OpenAI launches enterprise agent platform with usage-based pricing",
        "Anthropic cuts Claude API prices 40% for batch workloads",
    ]
    assert not any("morning routine" in i.title for i in kept)


def test_x_timeline_engagement_ranking_and_links():
    data = json.loads((FIX / "x_timeline_sample.json").read_text(encoding="utf-8").replace(
        "__RECENT__", RECENT.strftime("%Y-%m-%dT%H:%M:%S.000Z")))
    client = x_ingest.XClient("token")
    client._get = MagicMock(side_effect=lambda path, params: {"data": [{"id": "42", "username": "emollick"}]}
                            if path == "/users/by" else data)
    # fetch_top_posts builds its own XClient — hand it ours so no real HTTP happens.
    with patch.object(x_ingest, "require_env", return_value="token"), \
         patch.object(x_ingest, "XClient", return_value=client):
        items = x_ingest.fetch_top_posts(CFG)
    # The X top-N cut is engagement-only, so the 50k-like "gm" post leads here…
    assert items[0].summary.startswith("gm") and items[0].engagement > items[1].engagement
    thread = next(i for i in items if "earnings" in i.summary)
    assert thread.url == "https://www.oneusefulthing.org/p/enterprise-ai-earnings"  # external link preferred
    long_post = next(i for i in items if "NVIDIA" in i.summary)
    assert long_post.url == "https://x.com/emollick/status/1003"  # no external link → post URL
    assert long_post.title.startswith("NVIDIA announced")            # note_tweet text used
    # …and the relevance scorer is what removes it, despite the likes.
    ranked = rank_and_filter(items, CFG)
    assert {i.url for i in ranked} == {thread.url, long_post.url}
    assert not any(i.summary.startswith("gm") for i in ranked)


def test_gmail_newsletter_splits_into_stories():
    html = (FIX / "newsletter_email.html").read_text(encoding="utf-8")
    msg = {
        "id": "m1", "internalDate": str(int(RECENT.timestamp() * 1000)),
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [{"name": "From", "value": "TLDR AI <dan@tldr.tech>"},
                        {"name": "Subject", "value": "OpenAI agents, Anthropic pricing"},
                        {"name": "Date", "value": format_datetime(RECENT)}],
            "parts": [
                {"mimeType": "text/plain", "body": {"data": base64.urlsafe_b64encode(b"plain").decode()}},
                {"mimeType": "text/html", "body": {"data": base64.urlsafe_b64encode(html.encode()).decode()}},
            ],
        },
    }
    items = email_to_items(msg, "TLDR AI (email)", 1.2)
    assert [i.title for i in items] == ["OpenAI launches enterprise agent platform", "Anthropic cuts batch prices 40%"]
    assert items[0].url == "https://openai.com/blog/agents-enterprise"       # tracking links skipped
    assert items[1].url == "https://www.anthropic.com/news/batch-pricing"
    assert "http" not in items[0].summary and items[0].published.date() == RECENT.date()


def test_gmail_fallback_when_no_pattern():
    assert split_stories("Just a plain email with no headlines at all.", "tldr.tech") == []
