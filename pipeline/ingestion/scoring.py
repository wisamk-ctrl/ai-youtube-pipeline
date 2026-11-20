"""
Phase 1c — relevance scoring and noise filtering.

A transparent, deterministic scorer (no LLM) runs first, because it is free,
fast, and debuggable: every item carries a `score_breakdown` so you can see
*why* something made or missed the cut. The LLM in Phase 2 then does the
editorial judgement on the much smaller survivor set.

score = (topic_relevance + regional_bonus + engagement + recency) × source_weight × publisher_tier − noise_penalty

publisher_tier comes from config/publishers.yaml: A (wires, primary sources) 1.3, B (trade
press) 1.0, C (aggregators, unknown outlets) 0.6. Near-duplicate headlines (syndicated copies
of one wire story) are counted once: the best-scored copy is kept.

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

from pipeline.ingestion.publishers import load_publishers
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
    r"\b(sovereign|on-premises|private cloud|data sovereignty)\b": 1.0,   # the Gulf enterprise buying criterion
    r"\b(partnership|collaboration|acqui-?hire|ipo)\b": 0.5,
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
        "watchlist": 1.5 if item.entities else 0.0,   # a name we follow on purpose
        "enterprise": _keyword_score(item, "enterprise"),
        "regional": _keyword_score(item, "regional"),
        "engagement": _engagement_score(item),
        "recency": _recency_score(item, now),
        "noise": -_keyword_score(item, "noise"),
    }
    positive = parts["watchlist"] + parts["enterprise"] + parts["regional"] + parts["engagement"] + parts["recency"]
    tier_w = load_publishers().weight(item)
    item.score = round(positive * item.source_weight * tier_w + parts["noise"], 3)
    item.score_breakdown = {k: round(v, 3) for k, v in parts.items()} | {"publisher_tier": tier_w}
    return item


def _is_duplicate(a: NewsItem, b: NewsItem, threshold: float) -> bool:
    """Same link, or near-identical headline (the same launch covered by 3 newsletters)."""
    if a.url.split("?")[0].rstrip("/") == b.url.split("?")[0].rstrip("/"):
        return True
    return SequenceMatcher(None, a.normalized_title, b.normalized_title).ratio() >= threshold


# Story size (2026-11-20): W47's 30 seats went to 8 AWS blog posts, 6 NVIDIA posts and GitHub release notes while
# the Anthropic IPO, carried by 117 articles, was left out. Headlines that share two key words tell one story;
# the number of different outlets carrying it is the strongest sign it matters.
_STORY_STOP = set("""and the for with its how are can now new from after over what why who you our not has was get
set top all out off via its than that this into about amid says said will just more most first year week today
news update report agent model chip data tech 2026 2025 launche launch open use using help""".split())


def _key_words(title: str) -> set[str]:
    out = set()
    for w in re.sub(r"[^a-z0-9 ]+", " ", title.lower()).split():
        w = w[:-1] if w.endswith("s") and len(w) > 4 else w
        if len(w) >= 3 and w not in _STORY_STOP:
            out.add(w)
    return out


class _Stories:
    """Which items tell the same story: two shared key words, ignoring words in more than `common` of headlines."""

    def __init__(self, items: list[NewsItem], common: float = 0.2):
        self.words = {i.id: _key_words(i.title) for i in items}
        df: dict[str, int] = {}
        for ws in self.words.values():
            for w in ws:
                df[w] = df.get(w, 0) + 1
        too_common = {w for w, n in df.items() if len(items) >= 20 and n / len(items) > common}
        self.words = {k: ws - too_common for k, ws in self.words.items()}
        self.by_id = {i.id: i for i in items}
        self.index: dict[str, list[NewsItem]] = {}
        for i in items:
            for w in self.words[i.id]:
                self.index.setdefault(w, []).append(i)

    def same(self, a: NewsItem, b: NewsItem) -> bool:
        return len(self.words.get(a.id, set()) & self.words.get(b.id, set())) >= 2

    def outlets(self, item: NewsItem) -> int:
        shared: dict[str, int] = {}
        for w in self.words.get(item.id, ()):
            for other in self.index.get(w, ()):
                shared[other.id] = shared.get(other.id, 0) + 1
        return len({item.source} | {self.by_id[k].source for k, n in shared.items() if n >= 2})


def rank_and_filter(items: list[NewsItem], cfg: dict[str, Any], flagged: set[str] | None = None) -> list[NewsItem]:
    """Score everything, add the story-size bonus, drop noise, de-duplicate (keeping the best-scored copy), cap
    seats per source and per story, reserve seats for the stories the news watch flagged, cap the list."""
    s = cfg["scoring"]
    now = datetime.now(timezone.utc)
    titled = [i for i in items if i.title.strip()]
    stories = _Stories(titled)
    bonus_w = float(s.get("coverage_bonus", 0))
    for i in titled:
        score_item(i, now)
        outlets = min(stories.outlets(i), 64) if bonus_w else 1
        i.score_breakdown["coverage"] = round(bonus_w * math.log2(outlets), 3)
        i.score = round(i.score + i.score_breakdown["coverage"], 3)
    scored = sorted(titled, key=lambda i: i.score, reverse=True)

    per_source, per_story = s.get("max_per_source"), s.get("max_per_story")
    kept: list[NewsItem] = []
    for item in scored:
        if item.score < s["min_score"] and item.id not in (flagged or set()):
            continue
        # Because the list is sorted, the first copy of a story we keep is the highest-scored one.
        if any(_is_duplicate(item, k, s["dedupe_similarity"]) for k in kept):
            continue
        if per_source and sum(1 for k in kept if k.source == item.source) >= per_source:
            continue
        if per_story and sum(1 for k in kept if stories.same(item, k)) >= per_story:
            continue
        kept.append(item)

    reserved: list[NewsItem] = []
    for item in kept:
        if len(reserved) >= int(s.get("flagged_seats", 0)):
            break
        if item.id in (flagged or set()) and not any(stories.same(item, r) for r in reserved):
            reserved.append(item)
    kept = _apply_track_quotas(kept, s.get("min_per_track", {}), s["max_items"], reserved)
    log.info("Scoring: %d in → %d kept (min_score=%.1f, %d flagged seats)", len(items), len(kept), s["min_score"],
             len(reserved))
    return kept


def _apply_track_quotas(ranked: list[NewsItem], quotas: dict[str, int], cap: int,
                        reserved: list[NewsItem] | None = None) -> list[NewsItem]:
    """Reserve seats per track so every beat of the episode has material, then fill by score.

    `ranked` is already sorted and de-duplicated. Each track's best N items are taken
    first (N from settings), the rest of the cap is filled with the highest remaining
    scores regardless of track. Score order is restored at the end so the editor
    still sees the strongest story first.
    """
    chosen: list[NewsItem] = list(reserved or [])
    for track, n in quotas.items():
        chosen += [i for i in ranked if i.track == track and i not in chosen][:n]
    for item in ranked:
        if len(chosen) >= cap:
            break
        if item not in chosen:
            chosen.append(item)
    chosen = chosen[:max(cap, sum(quotas.values()) + len(reserved or []))]
    return sorted(chosen, key=lambda i: i.score, reverse=True)
