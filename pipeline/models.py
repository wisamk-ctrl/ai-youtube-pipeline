"""
Shared data model passed between the three phases.

Every source (RSS entry, X post) is normalised into a NewsItem so the scorer
and the scripting engine never need to know where an item came from.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class NewsItem:
    source: str                       # "TLDR AI", "@emollick", ...
    source_type: Literal["rss", "x"]
    title: str                        # headline (for X posts: the first line of the post)
    summary: str                      # plain-text body, HTML stripped
    url: str
    published: datetime               # always timezone-aware UTC
    author: str = ""
    engagement: int = 0               # X: likes + 2×reposts + 3×quotes; RSS: 0
    source_weight: float = 1.0        # credibility multiplier from settings.yaml
    score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)

    @property
    def id(self) -> str:
        """Stable short ID, used by the LLM to reference items it selected."""
        return hashlib.sha1(self.url.encode("utf-8")).hexdigest()[:10]

    @property
    def normalized_title(self) -> str:
        """Lower-cased, punctuation-free title for near-duplicate detection."""
        return re.sub(r"[^\w\s]", "", self.title.lower()).strip()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["id"] = self.id
        d["published"] = self.published.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "NewsItem":
        d = {k: v for k, v in d.items() if k != "id"}
        d["published"] = datetime.fromisoformat(d["published"])
        return cls(**d)
