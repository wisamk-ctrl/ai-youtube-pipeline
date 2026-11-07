"""
Publisher tiers (config/publishers.yaml): who said it, and how much that counts.

  A  wire / primary source   weight 1.3   may be the on-screen source credit
  B  trade press             weight 1.0   may be the on-screen source credit
  C  aggregator / unknown    weight 0.6   a lead only: never the on-screen source card

Radar items (pipeline/radar) are summaries we wrote ourselves: they are never citable,
neither in the source map nor on screen; a claim cites the underlying items instead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from pipeline.config import ROOT
from pipeline.models import NewsItem

DEFAULT_PATH = ROOT / "config" / "publishers.yaml"


def _key(name: str) -> str:
    # "Google News · Anthropic" (publisher not split off) stays unknown: the name is the
    # search, not the outlet; its news.google.com URL makes it tier C.
    return re.sub(r"[^\w]+", "", (name or "").lower())


@dataclass(frozen=True)
class Publisher:
    name: str
    tier: str
    aliases: tuple[str, ...] = ()
    ar: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()

    def keys(self) -> set[str]:
        return {_key(n) for n in (self.name, *self.aliases)}


@dataclass
class Publishers:
    publishers: list[Publisher]
    weights: dict[str, float]
    default_tier: str = "C"

    def lookup(self, item: NewsItem) -> Publisher | None:
        """By source name first (Google News items carry the publisher there), then by URL domain."""
        k = _key(item.source)
        for p in self.publishers:
            if k and k in p.keys():
                return p
        host = (urlparse(item.url).hostname or "").lower().removeprefix("www.")
        for p in self.publishers:
            if any(host == d or host.endswith("." + d) for d in p.domains):
                return p
        return None

    def tier(self, item: NewsItem) -> str:
        if is_radar(item):
            return "R"
        p = self.lookup(item)
        return p.tier if p else self.default_tier

    def weight(self, item: NewsItem) -> float:
        """Radar items keep weight 1: they are leads the editor should see, not sources."""
        t = self.tier(item)
        return 1.0 if t == "R" else float(self.weights.get(t, self.weights.get(self.default_tier, 0.6)))

    def named_in(self, text: str) -> list[Publisher]:
        """Publishers a sentence names (Arabic or Latin spelling), for attribution checks."""
        out = []
        for p in self.publishers:
            for n in (*p.ar, p.name, *p.aliases):
                if len(n) < 3:      # 'AP', 'FT' are too ambiguous to find in running text
                    continue
                esc = re.escape(n)
                rx = rf"\b{esc}\b" if n.isascii() else rf"(?<![\w؀-ۿ])(?:[وبلف]?(?:ال)?){esc}(?![\w؀-ۿ])"
                if re.search(rx, text, re.I):
                    out.append(p)
                    break
        return out

    def matches(self, p: Publisher, item: NewsItem) -> bool:
        found = self.lookup(item)
        return found is not None and found.name == p.name


def is_radar(item: NewsItem) -> bool:
    return item.track == "radar" or item.source == "Radar" or item.url.startswith("radar://")


def load_publishers(path: Path | None = None) -> Publishers:
    return _load(str(path or DEFAULT_PATH))


@lru_cache(maxsize=4)
def _load(path: str) -> Publishers:
    p = Path(path)
    raw: dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    weights = {t: float(v.get("weight", 1.0)) for t, v in (raw.get("tiers") or {}).items()} or {"A": 1.3, "B": 1.0, "C": 0.6}
    pubs = [Publisher(name=e["name"], tier=str(e.get("tier", "C")), aliases=tuple(e.get("aliases", [])),
                      ar=tuple(e.get("ar", [])), domains=tuple(d.lower() for d in e.get("domains", [])))
            for e in raw.get("publishers") or []]
    return Publishers(pubs, weights, str(raw.get("default_tier", "C")))


def tier_of(item: NewsItem) -> str:
    return load_publishers().tier(item)


def on_screen_ok(item: NewsItem) -> bool:
    """May this item be the on-screen source credit? Tier A/B only; never radar, never tier C."""
    return tier_of(item) in ("A", "B")
