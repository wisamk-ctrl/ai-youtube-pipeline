"""
Phase 1c — relevance scoring and noise filtering.

A transparent, deterministic scorer (no LLM) runs first, because it is free,
fast, and debuggable: every item carries a `score_breakdown` so you can see
*why* something made or missed the cut. The LLM in Phase 2 then does the
editorial judgement on the much smaller survivor set.

score = (topic_relevance + regional_bonus + engagement + recency) × source_weight − noise_penalty

Tune the keyword tables below to your audience. They are weighted toward what
an Arabic-speaking enterprise/tech viewer acts on: model launches, enterprise
adoption, infrastructure, regulation, and anything touching the GCC/MENA.
"""

from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any

from pipeline.models import NewsItem

log = logging.getLogger(__name__)

# keyword/regex → weight. Matched case-insensitively on title + summary.
# Title matches count double (a headline is a stronger signal than a passing mention).
ENTERPRISE_SIGNALS: dict[str, float] = {
    r"\benterprise\b": 1.5,
    r"\bagent(s|ic)?\b": 1.2,
    r"\b(api|sdk)\b": 0.8,
    r"\b(launch|launches|released?|unveil\w*|announce\w*|general availability|\bGA\b)": 1.0,
    r"\b(gpt|claude|gemini|llama|mistral|qwen|deepseek|grok)\b": 1.0,
    r"\b(openai|anthropic|google deepmind|meta ai|microsoft|nvidia|aws|apple)\b": 0.8,
    r"\b(funding|raises?|acquisition|acquires?|valuation|ipo)\b": 1.0,
    r"\b(regulation|eu ai act|policy|compliance|governance|copyright)\b": 1.2,
    r"\b(gpu|chips?|data ?cent(er|re)s?|inference|compute)\b": 0.9,
    r"\b(security|jailbreak|vulnerabilit\w+|privacy)\b": 0.9,
    r"\b(benchmark|state[- ]of[- ]the[- ]art|sota|reasoning)\b": 0.6,
    r"\b(open[- ]source|open[- ]weights?)\b": 0.8,
    r"\b(pricing|price cut|cost)\b": 0.7,
    r"\b(productivity|roi|adoption|workforce|jobs)\b": 0.8,
}

# The channel's differentiator: stories with a regional angle get a bonus.
REGIONAL_SIGNALS: dict[str, float] = {
    r"\b(uae|emirates|abu dhabi|dubai|saudi|ksa|riyadh|qatar|doha|bahrain|kuwait|oman|egypt|gcc|mena|middle east)\b": 2.0,
    r"\b(arabic|falcon|jais|g42|mbzuai|tii|humain|sdaia|core42)\b": 2.0,
}

# Patterns that indicate low-value content for a news roundup.
NOISE_SIGNALS: dict[str, float] = {
    r"\b(giveaway|meme|lol|lmao)\b": 2.0,
    r"\b(webinar|sponsor(ed)?|promo code|discount|affiliate|sign up now)\b": 2.5,
    r"\b(we'?re hiring|job opening|apply now)\b": 2.5,
    r"🧵|\bthread\b": 0.5,          # threads are often opinion, not news
    r"^\s*(gm|good morning)\b": 3.0,
}

_COMPILED = {
    name: [(re.compile(p, re.IGNORECASE), w) for p, w in table.items()]
    for name, table in (
        ("enterprise", ENTERPRISE_SIGNALS),
        ("regional", REGIONAL_SIGNALS),
        ("noise", NOISE_SIGNALS),
    )
}


def _keyword_score(item: NewsItem, table: str) -> float:
    total = 0.0
    for rx, weight in _COMPILED[table]:
        if rx.search(item.title):
            total += 2 * weight
        elif rx.search(item.summary):
            total += weight
    return total


def _recency_score(item: NewsItem, now: datetime) -> float:
    """Exponential decay with a ~3.5-day half-life: Monday's news still counts on Sunday, less."""
    age_days = max((now - item.published).total_seconds() / 86400, 0)
    return 1.5 * math.exp(-age_days / 5)


def _engagement_score(item: NewsItem) -> float:
    """Log-scaled so a 50k-like post doesn't drown out a 2k-like but more relevant one."""
    return math.log10(1 + item.engagement) * 0.6


def score_item(item: NewsItem, now: datetime | None = None) -> NewsItem:
    now = now or datetime.now(timezone.utc)
    parts = {
        "enterprise": _keyword_score(item, "enterprise"),
        "regional": _keyword_score(item, "regional"),
        "engagement": _engagement_score(item),
        "recency": _recency_score(item, now),
        "noise": -_keyword_score(item, "noise"),
    }
    positive = parts["enterprise"] + parts["regional"] + parts["engagement"] + parts["recency"]
    item.score = round(positive * item.source_weight + parts["noise"], 3)
    item.score_breakdown = {k: round(v, 3) for k, v in parts.items()}
    return item


def _is_duplicate(a: NewsItem, b: NewsItem, threshold: float) -> bool:
    """Same link, or near-identical headline (the same launch covered by 3 newsletters)."""
    if a.url.split("?")[0].rstrip("/") == b.url.split("?")[0].rstrip("/"):
        return True
    return SequenceMatcher(None, a.normalized_title, b.normalized_title).ratio() >= threshold


def rank_and_filter(items: list[NewsItem], cfg: dict[str, Any]) -> list[NewsItem]:
    """Score everything, drop noise, de-duplicate (keeping the best-scored copy), cap the list."""
    s = cfg["scoring"]
    now = datetime.now(timezone.utc)

    scored = sorted((score_item(i, now) for i in items if i.title.strip()), key=lambda i: i.score, reverse=True)

    kept: list[NewsItem] = []
    for item in scored:
        if item.score < s["min_score"]:
            continue
        # Because the list is sorted, the first copy of a story we keep is the highest-scored one.
        if any(_is_duplicate(item, k, s["dedupe_similarity"]) for k in kept):
            continue
        kept.append(item)
        if len(kept) >= s["max_items"]:
            break

    log.info("Scoring: %d in → %d kept (min_score=%.1f)", len(items), len(kept), s["min_score"])
    return kept
