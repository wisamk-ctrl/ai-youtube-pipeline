"""Step 1 of the ranking (docs/plans/2026-11-22-news-ranking.md): group the week's scored items into stories.

Stories are ranked, never articles. How many outlets carry a story is recorded as a signal for the evidence
criterion and for the founder's eye; it is never added to or multiplied into the story's total.

An item joins the first story whose lead headline it shares two key words with, one of them a name, or
duplicates. Comparing against the lead only keeps one loose headline from chaining unrelated stories together.

2026-11-23, measured on the live W48 items: with any two shared words, verbs tied unrelated stories together
(ServiceNow "raises ... sees" sat inside an IMF story; "Saudi Arabia announces new tax" inside the SDAIA
universities story). So one shared word must be a name (a word written with a capital inside sentence-case
headlines), and two words that name one thing ("Saudi Arabia", "Wall Street", "Claude Code") count once.
One event told under different headlines is still split here; the judge names those and rank.merge_same joins them.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from pipeline.ingestion.publishers import load_publishers
from pipeline.ingestion.scoring import _STORY_STOP, _Stories, _is_duplicate, _key_words, region_of
from pipeline.models import NewsItem
from pipeline.ranking.rank import opts


# Words too general to tie two headlines together (W47 dry run: "artificial intelligence" alone merged a Saudi
# university programme with chip and China stories).
_GENERIC = set("artificial intelligence initiative company firm tech technology digital global world market "
               "business industry announce announced plan plans major billion million ceo chief".split())


def _tokens(title: str) -> list[tuple[str, str, int]]:
    """(key word, as written, position) for each key word of a headline, in order (scoring._key_words' rule)."""
    out = []
    for n, raw in enumerate(re.sub(r"[^A-Za-z0-9 ]+", " ", title).split()):
        w = raw.lower()
        w = w[:-1] if w.endswith("s") and len(w) > 4 else w
        if len(w) >= 3 and w not in _STORY_STOP:
            out.append((w, raw, n))
    return out


class _Vocab:
    """The week's headlines as word sets: generic and too-common words dropped, a pair of words that names one
    thing joined into one, and the set of words that are names."""

    def __init__(self, pool: list[NewsItem]):
        base = _Stories(pool).words
        toks = {i.id: _tokens(i.title) for i in pool}
        df: dict[str, int] = {}
        seen: dict[str, int] = {}
        cap: dict[str, int] = {}
        pair: dict[tuple[str, str], int] = {}
        for t in toks.values():
            for w in {w for w, _, _ in t}:
                df[w] = df.get(w, 0) + 1
            for (a, _, n1), (b, _, n2) in zip(t, t[1:]):
                if n2 == n1 + 1 and a != b:
                    pair[(a, b)] = pair.get((a, b), 0) + 1
            inner = [raw for _, raw, n in t if n > 0]
            if not inner or sum(r[0].isupper() for r in inner) / len(inner) >= 0.7:
                continue                      # a Title Case headline says nothing about which words are names
            for w, raw, n in t:
                if n > 0:
                    seen[w] = seen.get(w, 0) + 1
                    cap[w] = cap.get(w, 0) + (raw[0].isupper() or (raw[0].isdigit() and not raw.isdigit()))
        # A name: capitalised wherever a sentence-case headline uses it; a word seen only in Title Case headlines
        # counts when it is rare (a product or company name in a press release).
        self.names = {w for w in df if (seen.get(w) and cap[w] / seen[w] >= 0.85) or (not seen.get(w) and df[w] <= 5)}
        joined = {p for p, c in pair.items() if c >= 3 and c / min(df[p[0]], df[p[1]]) >= 0.5}
        self.words: dict[str, set[str]] = {}
        for i in pool:
            ws = set(base[i.id]) - _GENERIC
            t = toks[i.id]
            for (a, _, n1), (b, _, n2) in zip(t, t[1:]):
                if n2 == n1 + 1 and (a, b) in joined:
                    ws -= {a, b}
                    ws.add(f"{a}_{b}")
                    if a in self.names or b in self.names:
                        self.names.add(f"{a}_{b}")
            self.words[i.id] = ws

    def same_story(self, a: NewsItem, b: NewsItem) -> bool:
        """Two shared specific words, at least one of them a name. (A stricter share-of-headline test was tried
        on W47 and split the Anthropic IPO into twelve stories.)"""
        shared = self.words[a.id] & self.words[b.id]
        return len(shared) >= 2 and bool(shared & self.names)


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
    words = _Vocab(pool)
    groups: list[list[NewsItem]] = []
    for it in pool:
        for g in groups:
            lead = g[0]
            if words.same_story(it, lead) or (
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
