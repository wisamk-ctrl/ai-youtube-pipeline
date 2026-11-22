"""AI relevance filter for broad regional tech/business outlets (founder 2026-11-22: more local coverage)."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingestion import rss_ingest, watch_sources  # noqa: E402
from pipeline.ingestion.ai_filter import is_ai_relevant  # noqa: E402
from pipeline.ingestion.publishers import load_publishers  # noqa: E402
from pipeline.models import NewsItem  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NOW = datetime.now(timezone.utc)


@pytest.mark.parametrize("title", [
    "Dubai Taxi Company to train 400 employees in AI under new programme",
    "UAE AI Office and UNDP announce initiative to reach 100,000 Arab women",
    "Anthropic IPO raises $81.3 billion as shares jump on Nasdaq debut",
    "Core42 bets on partners to close the UAE's sovereign cloud gap",
    "Sharjah free zone targets 400MW data centre",
    "Saudi Arabia's Humain signs chip deal with Nvidia",
    "How generative models are changing Gulf banking",
    "CNTXT AI تتعهد باستثمار أكثر من 180 مليون درهم",
    "الإمارات تطلق استراتيجية جديدة للذكاء الاصطناعي",
    "مصر تعتمد على الذكاء الإصطناعي في الخدمات الحكومية",
    "شركة ناشئة أردنية تطور نموذجاً لغوياً باللهجة المحلية",
    "أوبن إيه آي تطلق نسخة عربية من تشات جي بي تي",
    "OpenAI, Dots kişisel yapay zeka ajanlarını ChatGPT'ye ekliyor",
    "Türk girişimi büyük dil modeli için yatırım aldı",
])
def test_ai_headlines_pass(title):
    assert is_ai_relevant(title)


@pytest.mark.parametrize("title", [
    "Dubai Run 2026: Thousands take over Sheikh Zayed Road",
    "Saudi Arabia deports 11,915 illegal residents in a week",
    "Air India flight AI171 diverted to Dubai",
    "Falcon festival draws record crowds in Abu Dhabi",
    "Diriyah cancels $200m hotel construction contract",
    "وزير الداخلية العراقي يوجه بسحب القوات القتالية",
    "رقائق البطاطس الأردنية تغزو أسواق الخليج",
    "Merkez Bankası faiz kararını açıkladı",
])
def test_non_ai_headlines_fail(title):
    assert not is_ai_relevant(title)


def test_one_passing_mention_in_the_body_is_not_enough_two_are():
    title = "Gulf fund closes $300m vehicle"
    assert not is_ai_relevant(title, "The fund backs fintech, AI and healthcare founders across the GCC.")
    assert is_ai_relevant(title, "It will back artificial intelligence start-ups; half the fund goes to AI chips.")
    assert is_ai_relevant("صندوق جديد بقيمة 300 مليون دولار",
                          "يستثمر الصندوق في الذكاء الاصطناعي، وخصوصاً شركات تعلم الآلة في المنطقة.")


def test_arabic_diacritics_and_tatweel_do_not_hide_a_match():
    assert is_ai_relevant("السعودية تستثمر في الذّكاء الاصطـناعي")


def _feed(*entries: tuple[str, str]) -> bytes:
    from email.utils import format_datetime
    items = "".join(f"<item><title>{t}</title><link>https://example.com/{n}</link><description>{d}</description>"
                    f"<pubDate>{format_datetime(NOW - timedelta(days=1))}</pubDate></item>"
                    for n, (t, d) in enumerate(entries))
    return f'<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>{items}</channel></rss>'.encode()


def _cfg(feed: dict) -> dict:
    return {"ingestion": {"lookback_days": 7, "request_timeout_s": 5, "rss_feeds": [feed]}}


MIXED = _feed(("UAE launches national AI agent platform", "..."),
              ("Dubai Run 2026 draws thousands", "..."),
              ("الأردن يطلق مركزاً للذكاء الاصطناعي", "..."))


def test_ai_only_feed_keeps_ai_items_and_tags_the_region():
    resp = MagicMock(content=MIXED, raise_for_status=lambda: None)
    with patch.object(rss_ingest.requests, "get", return_value=resp):
        items = rss_ingest.fetch_all_feeds(_cfg({"name": "Gulf News", "url": "https://gulfnews.com/feed",
                                                 "ai_only": True, "region": "gulf"}))
    assert [i.title for i in items] == ["UAE launches national AI agent platform", "الأردن يطلق مركزاً للذكاء الاصطناعي"]
    assert {i.region for i in items} == {"gulf"}


def test_feeds_without_the_flag_are_unchanged():
    resp = MagicMock(content=MIXED, raise_for_status=lambda: None)
    with patch.object(rss_ingest.requests, "get", return_value=resp):
        items = rss_ingest.fetch_all_feeds(_cfg({"name": "TLDR AI", "url": "https://tldr.tech/api/rss/ai"}))
    assert len(items) == 3 and {i.region for i in items} == {""}


def test_ai_only_site_search_filters_before_the_item_cap():
    def item(n: int, title: str) -> NewsItem:
        return NewsItem(source="Google News · Khaleej Times", source_type="rss", title=f"{title} - Khaleej Times",
                        summary="", url=f"https://news.google.com/{n}", published=NOW)
    found = [item(0, "Dubai Run 2026"), item(1, "Gold price today"), item(2, "UAE hospitals adopt AI triage"),
             item(3, "Etisalat launches Arabic chatbot powered by a large language model")]
    cfg = {"ingestion": {"lookback_days": 7, "request_timeout_s": 5, "watchlist": {"fetch_articles": {"enabled": False}},
                         "google_news_sites": [{"name": "Khaleej Times", "query": "site:khaleejtimes.com",
                                                "region": "gulf", "ai_only": True, "max_items": 2}]},
           "scoring": {"dedupe_similarity": 0.82}}
    with patch.object(watch_sources, "fetch_feed", return_value=found), \
         patch.object(watch_sources.time, "sleep", lambda s: None):
        items = watch_sources.fetch_site_queries(cfg)
    assert [i.title for i in items] == ["UAE hospitals adopt AI triage",
                                        "Etisalat launches Arabic chatbot powered by a large language model"]
    assert all(i.source == "Khaleej Times" and i.region == "gulf" for i in items)


def test_every_ai_only_outlet_has_a_known_publisher_tier():
    """A new outlet must be in config/publishers.yaml, or it silently falls to tier C (never credited on screen)."""
    ing = yaml.safe_load((ROOT / "config/settings.yaml").read_text(encoding="utf-8"))["ingestion"]
    flagged = [s for s in [*ing["rss_feeds"], *ing["google_news_sites"]] if s.get("ai_only")]
    assert flagged, "no ai_only outlets configured"
    pubs = load_publishers()
    for s in flagged:
        probe = NewsItem(source=s["name"], source_type="rss", title="t", summary="", url=s.get("url", ""),
                         published=NOW)
        assert pubs.lookup(probe) is not None, f"{s['name']} has no entry in config/publishers.yaml"
        assert s.get("region"), f"{s['name']} has no region"
