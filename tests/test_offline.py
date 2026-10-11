"""Offline tests: no network, no API keys. Run with `pytest` from ai-youtube-pipeline/."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingestion.scoring import rank_and_filter, score_item  # noqa: E402
from pipeline.models import NewsItem  # noqa: E402
from pipeline.script_format import (  # noqa: E402
    chunk_text, count_spoken_words, extract_cues, spoken_text, to_tts_text,
)

NOW = datetime.now(timezone.utc)
CFG = {"scoring": {"min_score": 2.0, "max_items": 25, "dedupe_similarity": 0.82}}


def item(title: str, summary: str = "", url: str | None = None, days_old: float = 1, **kw) -> NewsItem:
    return NewsItem(source="test", source_type="rss", title=title, summary=summary,
                    url=url or f"https://example.com/{abs(hash(title))}",
                    published=NOW - timedelta(days=days_old), **kw)


def test_enterprise_story_outscores_noise():
    good = score_item(item("OpenAI launches enterprise agents API with new pricing"), NOW)
    noise = score_item(item("gm! giveaway thread 🧵", "sponsored webinar, promo code inside"), NOW)
    assert good.score > 2.0 > noise.score
    assert good.score_breakdown["enterprise"] > 0
    assert noise.score_breakdown["noise"] < 0


def test_regional_bonus():
    plain = score_item(item("New model released"), NOW)
    regional = score_item(item("New Arabic model released by G42 in Abu Dhabi"), NOW)
    assert regional.score > plain.score


def test_dedupe_keeps_best_copy():
    a = item("Anthropic releases Claude enterprise agent platform", engagement=0, source_weight=1.0)
    b = item("Anthropic releases Claude enterprise agent platform!", source_weight=1.5)
    kept = rank_and_filter([a, b], CFG)
    assert len(kept) == 1 and kept[0].source_weight == 1.5


def test_roundtrip_dict():
    i = item("x launches api")
    assert NewsItem.from_dict(i.to_dict()).url == i.url


SCRIPT = """[Section: المقدمة]
مرحباً بكم في حلقة جديدة.
[Pause]
[Show B-Roll: OpenAI logo]
أعلنت OpenAI اليوم عن نموذج جديد؟ نعم.
[Pause 2s]
[On-Screen Text: 40 مليار دولار]
وهذا مهم للشركات."""


def test_spoken_text_strips_markers():
    spoken = spoken_text(SCRIPT)
    assert "[" not in spoken and "B-Roll" not in spoken
    assert count_spoken_words(SCRIPT) == len(spoken.split())


def test_tts_pauses():
    ssml = to_tts_text(SCRIPT, "ssml", 0.8)
    assert '<break time="0.8s"/>' in ssml and '<break time="2.0s"/>' in ssml
    assert "Show B-Roll" not in ssml
    assert "..." in to_tts_text(SCRIPT, "ellipsis")


def test_cues_have_kinds_and_times():
    cues = extract_cues(SCRIPT, 130)
    kinds = [c.kind for c in cues]
    assert kinds == ["section", "pause", "broll", "pause", "onscreen"]
    assert cues[2].text == "OpenAI logo" and cues[2].at_word == 5
    assert cues[-1].at_seconds > cues[0].at_seconds


def test_chunking_respects_limit_and_sentences():
    text = " ".join(["هذه جملة عربية قصيرة."] * 200)
    chunks = chunk_text(text, 300)
    assert all(len(c) <= 300 for c in chunks)
    assert all(c.endswith(".") for c in chunks)
    assert " ".join(chunks) == text
