"""Is a news story one we already covered? Shared by the news watch (pipeline/breaking.py) and the dashboard's
"needs you" list (scripts/channel.py, which runs with only the standard library and requests)."""
from __future__ import annotations

import re


def _norm(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", t.lower()).strip()


STOP = set("about after again also amid among been being but could from have here into just like more most much "
           "over says said some than that their them then there these they this those what when where which while "
           "will with would your news today week explained update updated report reports".split())


def _words(title: str) -> set[str]:
    """Key words of a headline: four letters or more, no common words, plural 's' dropped."""
    out = set()
    for w in _norm(title).split():
        if len(w) >= 4 and w not in STOP:
            out.add(w[:-1] if w.endswith("s") and len(w) > 4 else w)
    return out


def is_repeat(titles: list[str], recent: list[str], shared: int = 2) -> bool:
    """A story already drafted lately under another headline: any of its headlines shares `shared` key words with
    one recent headline. 2026-11-20: five more outage drafts followed the posted outage Short, each under a new
    headline, because only an exact headline counted as done."""
    sets = [_words(r) for r in recent]
    return any(len(_words(t) & s) >= shared for t in titles for s in sets)
