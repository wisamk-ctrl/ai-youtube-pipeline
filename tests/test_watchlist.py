"""Watchlist: loading, matching, track quotas, Google News parsing (HTTP mocked)."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingestion import rss_ingest, watch_sources  # noqa: E402
from pipeline.ingestion.scoring import rank_and_filter  # noqa: E402
from pipeline.ingestion.watchlist import load_watchlist  # noqa: E402
from pipeline.models import NewsItem  # noqa: E402

NOW = datetime.now(timezone.utc)
W = load_watchlist()
CFG = {
    "ingestion": {"lookback_days": 7, "request_timeout_s": 5, "watchlist": {"max_per_entity": 8}},
    "scoring": {"min_score": 0, "max_items": 6, "dedupe_similarity": 0.82,
                "min_per_track": {"models": 2, "agents": 2, "chips": 1}},
}


def item(title: str, summary: str = "", track: str = "", score_hint: int = 0) -> NewsItem:
    i = NewsItem(source="t", source_type="rss", title=title, summary=summary,
                 url=f"https://e.com/{abs(hash(title))}", published=NOW - timedelta(days=1), engagement=score_hint)
    i.track = track
    return i


def test_watchlist_loads_three_tracks_with_gulf():
    tracks = {e.track for e in W.entities}
    assert tracks == {"models", "agents", "chips"}
    gulf = [e for e in W.entities if e.group == "gulf"]
    assert {e.name for e in gulf} >= {"G42", "TII", "Humain", "SDAIA", "MBZUAI"}
    assert all(e.weight == 1.3 for e in gulf)            # the group weight is applied
    assert W.labels_ar["models/gulf"].startswith("الخليج")


def test_tagging_sets_track_region_entities_and_weight():
    i = W.tag(item("Jais 2 released by Core42 for Arabic enterprises", "Built in Abu Dhabi."))
    assert i.track == "models" and i.region == "gulf" and i.entities == ["G42"]
    assert i.source_weight == 1.3
    j = W.tag(item("AMD unveils Instinct MI400 for inference", "Lisa Su on stage."))
    assert j.track == "chips" and "AMD" in j.entities
    k = W.tag(item("Farm robots get smarter", "Nothing about chips here."))
    assert k.track == "" and k.entities == []            # "Arm" must not match "Farm"


def test_arabic_alias_matches():
    i = W.tag(item("ديب سيك تطلق نموذجاً جديداً", ""))
    assert i.entities == ["DeepSeek"] and i.region == "cn"


def test_title_decides_track_when_summary_mentions_others():
    i = W.tag(item("OpenClaw 2.0 ships multi-agent planning", "Works with Claude and GPT models."))
    assert i.track == "agents" and i.region == "frameworks"
    assert set(i.entities) >= {"OpenClaw", "Anthropic", "OpenAI"}


def test_track_quotas_reserve_seats():
    items = [item(t, track="models", score_hint=10_000 - n) for n, t in enumerate(["GPT update", "Claude update", "Gemini update", "Llama update", "Grok update"])]
    items += [item(t, track="agents", score_hint=10 - n) for n, t in enumerate(["OpenClaw ships planner", "CrewAI adds memory", "n8n agent nodes arrive"])]
    items += [item("Chip story NVIDIA Blackwell", track="chips", score_hint=5)]
    kept = rank_and_filter(items, CFG)
    tracks = [i.track for i in kept]
    assert tracks.count("agents") >= 2 and tracks.count("chips") >= 1    # seats held despite low engagement
    assert len(kept) == 6 and kept[0].track == "models"                  # cap respected, best story first


def test_google_news_feed_parses_publisher_and_tags():
    xml = f'''<?xml version="1.0"?><rss version="2.0"><channel><title>"Mistral" AI</title>
    <item><title>Mistral unveils Large 4 - CNBC</title><link>https://news.google.com/rss/articles/abc</link>
    <pubDate>{format_datetime(NOW - timedelta(days=2))}</pubDate><description>Mistral launched a new open-weight model.</description></item>
    </channel></rss>'''.encode()
    resp = MagicMock(content=xml, raise_for_status=lambda: None)
    mistral = next(e for e in W.entities if e.name == "Mistral")
    with patch.object(rss_ingest.requests, "get", return_value=resp):
        items = watch_sources.fetch_google_news(W, CFG, entities=[mistral])
    assert len(items) == 1
    assert items[0].title == "Mistral unveils Large 4" and items[0].source == "CNBC"
    assert items[0].track == "models" and items[0].region == "eu" and items[0].entities == ["Mistral"]
    assert "when%3A7d" in watch_sources.google_news_url(mistral.news_query, 7)
