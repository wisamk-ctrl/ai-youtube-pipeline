"""Step 1 of the ranking (docs/plans/2026-11-22-news-ranking.md): group the week's scored items into stories.

Stories are ranked, never articles. How many outlets carry a story is recorded as a signal for the evidence
criterion and for the founder's eye; it is never added to or multiplied into the story's total.

An item joins the first story whose lead headline it shares two key words with (the rule the scorer already
uses, pipeline/ingestion/scoring.py `_Stories`) or duplicates. Comparing against the lead only keeps one loose
headline from chaining unrelated stories together.
"""
from __future__ import annotations

import hashlib
from typing import Any

from pipeline.ingestion.publishers import load_publishers
from pipeline.ingestion.scoring import _Stories, _is_duplicate, _key_words, region_of
from pipeline.models import NewsItem
from pipeline.ranking.rank import opts


# Words too general to tie two headlines together (W47 dry run: "artificial intelligence" alone merged a Saudi
# university programme with chip and China stories).
_GENERIC = set("artificial intelligence initiative company firm tech technology digital global world market "
               "business industry announce announced plan plans major billion million ceo chief".split())


def _same_story(a: set[str], b: set[str]) -> bool:
    """Two shared specific words (the scorer's rule, without the generic ones). A stricter share-of-headline
    test was tried on W47 and split the Anthropic IPO into twelve stories."""
    return len((a - _GENERIC) & (b - _GENERIC)) >= 2


def _regions(g: list[NewsItem]) -> list[str]:
    """The lead article's regions, plus any region at least half of the story's articles carry: one stray
    article must not hand a story the Africa or Türkiye seat."""
    of = lambda i: {r for r in (region_of(i), i.region) if r}
    count: dict[str, int] = {}
    for i in g:
        for r in of(i):
            count[r] = count.get(r, 0) + 1
    return sorted(of(g[0]) | {r for r, n in count.items() if n * 2 >= len(g)})


def _story_id(items: list[NewsItem], taken: set[str]) -> str:
    """Stable across re-runs: named after the story's earliest article, not its rank."""
    anchor = min(items, key=lambda i: (i.published, i.id))
    digest = hashlib.sha1(anchor.id.encode()).hexdigest()
    n = 4
    while "s" + digest[:n] in taken:
        n += 1
    return "s" + digest[:n]


def cluster(items: list[NewsItem], cfg: dict[str, Any], flagged: set[str] | None = None,
            covered: list[str] | None = None) -> list[dict[str, Any]]:
    """Scored items → at most `ranking.max_stories` stories, best lead first. Stories the news watch flagged and
    the Africa/Türkiye seats (`scoring.min_per_region`) are kept in the list even when their lead scores low."""
    o, s = opts(cfg), cfg["scoring"]
    flagged = flagged or set()
    pool = sorted((i for i in items if i.title.strip() and (i.score >= s["min_score"] or i.id in flagged)),
                  key=lambda i: (-i.score, i.id))
    words = _Stories(pool)
    groups: list[list[NewsItem]] = []
    for it in pool:
        for g in groups:
            lead = g[0]
            if _same_story(words.words[it.id], words.words[lead.id]) or (
                    (it.url == lead.url or words.words[it.id] & words.words[lead.id])
                    and _is_duplicate(it, lead, s["dedupe_similarity"])):
                g.append(it)
                break
        else:
            groups.append([it])

    pubs = load_publishers()
    covered_words = [(t, w) for t, w in ((t, _key_words(t)) for t in (covered or [])) if len(w) >= 2]
    stories: list[dict[str, Any]] = []
    for g in groups:
        lead_words = _key_words(g[0].title)
        tiers = sorted({pubs.tier(i) for i in g})
        outlets = list(dict.fromkeys((pubs.lookup(i).name if pubs.lookup(i) else i.source) for i in g))
        # The articles kept for the writer: the best-tier outlets first, one per outlet.
        seen, best = set(), []
        for i in sorted(g, key=lambda i: ("ABRC".find(pubs.tier(i)) % 9, -i.score, i.id)):
            name = pubs.lookup(i).name if pubs.lookup(i) else i.source
            if name not in seen:
                seen.add(name)
                best.append(i)
        stories.append({
            "title": g[0].title, "_items": g,
            "items": [i.to_dict() for i in best[:o["items_per_story"]]],
            "outlets": outlets, "outlet_count": len(outlets), "tiers": tiers,
            "verified": bool({"A", "B"} & set(tiers)),
            "regions": _regions(g),
            "flagged": any(i.id in flagged for i in g),
            "repeat": [t for t, w in covered_words if len(lead_words & w) >= 2][:3],
            "published": max(i.published for i in g).isoformat(),
            "lead_score": g[0].score,
        })

    keep = stories[:o["max_stories"]]
    extra = [st for st in stories[o["max_stories"]:] if st["flagged"]][:int(s.get("flagged_seats", 0))]
    for region, n in (s.get("min_per_region") or {}).items():
        have = sum(1 for st in keep + extra if region in st["regions"])
        extra += [st for st in stories if region in st["regions"] and st not in keep + extra][:max(0, int(n) - have)]
    keep = keep[:max(0, o["max_stories"] - len(extra))] + extra
    keep.sort(key=lambda st: -st["lead_score"])
    taken: set[str] = set()
    for st in keep:
        st["id"] = _story_id(st.pop("_items"), taken)
        taken.add(st["id"])
    return keep
