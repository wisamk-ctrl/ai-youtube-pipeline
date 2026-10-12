"""
The watchlist (config/watchlist.yaml): the names we follow on purpose, by track and group.

Two jobs:
  * flatten the YAML into Entity objects the source modules iterate over, and
  * tag any NewsItem (from any source) with the entities it mentions, its track and region.

Matching is whole-word and case-insensitive over name + aliases, so "Arm" does not
match "farm" and "Claude" tags Anthropic. Arabic names are matched too, for items
that come from Arabic-language sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from pipeline.config import ROOT
from pipeline.models import NewsItem

DEFAULT_PATH = ROOT / "config" / "watchlist.yaml"


@dataclass(frozen=True)
class Entity:
    name: str
    track: str            # models | agents | chips
    group: str            # us | eu | cn | gulf | frameworks | ...
    ar: str = ""
    aliases: tuple[str, ...] = ()
    query: str = ""
    rss: tuple[str, ...] = ()
    github: str = ""
    hf: str = ""
    x: str = ""
    weight: float = 1.0

    @property
    def terms(self) -> tuple[str, ...]:
        return (self.name, *self.aliases, *( (self.ar,) if self.ar else () ))

    @property
    def news_query(self) -> str:
        return self.query or (f'"{self.name}"' if " " in self.name else self.name)


@dataclass
class Watchlist:
    entities: list[Entity]
    labels_ar: dict[str, str] = field(default_factory=dict)   # "models" → Arabic label, "models/gulf" → ...

    def __post_init__(self) -> None:
        # One compiled regex per entity. \b doesn't work around Arabic letters, so the
        # Arabic terms use lookarounds on whitespace/punctuation instead.
        self._patterns: list[tuple[Entity, re.Pattern[str]]] = []
        for e in self.entities:
            parts = []
            for t in e.terms:
                esc = re.escape(t)
                parts.append(rf"\b{esc}\b" if t.isascii() else rf"(?<![\w؀-ۿ]){esc}(?![\w؀-ۿ])")
            self._patterns.append((e, re.compile("|".join(parts), re.IGNORECASE)))

    def by_track(self, track: str) -> list[Entity]:
        return [e for e in self.entities if e.track == track]

    def match(self, text: str) -> list[Entity]:
        return [e for e, rx in self._patterns if rx.search(text)]

    def tag(self, item: NewsItem) -> NewsItem:
        """Fill item.entities / track / region from its title + summary. Title matches decide the track."""
        in_title = self.match(item.title)
        hits = list({e.name: e for e in in_title + self.match(item.summary)}.values())
        if not hits:
            return item
        item.entities = sorted(e.name for e in hits)
        # The track comes from the headline when it names someone; otherwise from the
        # heaviest name in the body (so a Gulf mention outranks a passing "OpenAI").
        lead = in_title[0] if in_title else max(hits, key=lambda e: e.weight)
        item.track, item.region = lead.track, lead.group
        # The watchlist weight (e.g. Gulf 1.3) multiplies the source weight, once.
        item.source_weight = round(item.source_weight * max(e.weight for e in hits), 3)
        return item


def load_watchlist(path: Path | None = None) -> Watchlist:
    raw: dict[str, Any] = yaml.safe_load(open(path or DEFAULT_PATH, encoding="utf-8"))
    entities: list[Entity] = []
    labels: dict[str, str] = {}
    for track, tdef in raw["tracks"].items():
        labels[track] = tdef.get("label_ar", track)
        for group, gdef in tdef["groups"].items():
            labels[f"{track}/{group}"] = gdef.get("label_ar", group)
            gweight = float(gdef.get("weight", 1.0))
            for e in gdef["entities"]:
                entities.append(Entity(
                    name=e["name"], track=track, group=group, ar=e.get("ar", ""),
                    aliases=tuple(e.get("aliases", [])), query=e.get("query", ""),
                    rss=tuple(e.get("rss", [])), github=e.get("github", ""), hf=e.get("hf", ""),
                    x=e.get("x", ""), weight=float(e.get("weight", 1.0)) * gweight,
                ))
    return Watchlist(entities, labels)
