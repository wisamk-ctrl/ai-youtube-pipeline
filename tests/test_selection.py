"""Story selection (pipeline/ingestion/scoring.py). 2026-11-20: W47's 30 seats went to 8 AWS blog posts, 6 NVIDIA
posts and GitHub release notes, while the week's biggest story (the Anthropic IPO, 117 articles across WIRED, CNBC,
NYT, WSJ, Reuters) was left out: nothing counted how widely a story was covered."""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingestion import scoring  # noqa: E402
from pipeline.models import NewsItem  # noqa: E402

NOW = datetime.now(timezone.utc)
CFG = {"scoring": {"min_score": 2.0, "max_items": 6, "dedupe_similarity": 0.82, "coverage_bonus": 3.0,
                   "max_per_source": 2, "max_per_story": 2, "flagged_seats": 2}}


def it(title, source, summary="enterprise adoption of AI agents on the cloud", track="models"):
    return NewsItem(source=source, source_type="rss", title=title, summary=summary, url=f"https://x/{source}/{title}",
                    published=NOW - timedelta(hours=10), track=track)


def blog(n):
    topics = ["Bedrock guardrails", "SageMaker latency drift", "EKS GPU fractioning", "Nova pricing tiers",
              "AgentCore gateway", "Marketplace payments", "Inferentia clusters", "Lambda streaming"]
    return [it(f"How customers use {t} in production", "AWS blog",
               summary="enterprise agents openai anthropic microsoft nvidia aws cloud adoption deployment") for t in topics[:n]]


def ipo():
    heads = ["Anthropic IPO: shares jump in Nasdaq debut", "Anthropic's record IPO raises big questions",
             "Wall Street watches Anthropic IPO pricing", "Anthropic IPO values the AI lab at hundreds of billions",
             "Anthropic stock debut tests investor appetite for AI IPO"]
    return [it(h, src, summary="Anthropic listed its shares") for h, src in zip(heads, ["WIRED", "CNBC", "WSJ", "NYT", "Reuters"])]


def test_one_source_cannot_take_more_than_its_cap():
    kept = scoring.rank_and_filter(blog(8), CFG)
    assert sum(1 for k in kept if k.source == "AWS blog") <= 2


def test_widely_covered_story_outranks_a_single_blog_and_is_capped_per_story():
    kept = scoring.rank_and_filter(blog(8) + ipo(), CFG)
    ipo_kept = [k for k in kept if "anthropic" in k.title.lower()]
    assert 1 <= len(ipo_kept) <= 2
    assert kept[0] in ipo_kept                                   # the biggest story leads
    assert ipo_kept[0].score_breakdown["coverage"] > 0


def test_coverage_ignores_words_every_headline_shares():
    """'artificial intelligence' in a third of the week's headlines must not make each of those stories look big."""
    topics = ["farming", "banking", "schools", "hospitals", "football", "airports", "courts", "museums", "shipping",
              "insurance", "retail", "mining"]
    common = [it(f"Artificial intelligence reshapes {t}", f"Outlet {t}") for t in topics]
    other = [it(f"Unrelated headline about {t} {n}", f"Paper {t}{n}") for n, t in enumerate(topics * 2)]
    scoring.rank_and_filter(common + other, CFG)
    assert all(i.score_breakdown.get("coverage", 0) == 0 for i in common)


def test_flagged_story_gets_a_seat_even_when_it_scores_low():
    weak = it("Regulator opens inquiry into chatbot", "Small Outlet", summary="")
    kept = scoring.rank_and_filter(blog(3) + [it(f"Strong agents story {k} for enterprise", f"Src{k}") for k in range(6)]
                                   + [weak], {"scoring": {**CFG["scoring"], "min_score": 0.0}}, flagged={weak.id})
    assert weak in kept
