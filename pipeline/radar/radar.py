"""
Radar steps 3-5 — compare, score, surface, remember.

A candidate is a name that is NOT on the watchlist but shows up this week. It becomes
"radar news" when it clears the threshold agreed with the founder:

    mentioned as the SUBJECT by ≥ 2 independent sources this week
    AND at least one hard signal (HF trending, OpenRouter, GitHub stars, HN front page)

Memory (`data/radar_state.json`) remembers every candidate: first seen, per-week counts,
and a status you control — candidate | promoted | ignored. A promoted name should be
moved into config/watchlist.yaml; an ignored one is never surfaced again.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.config import ROOT
from pipeline.ingestion.watchlist import Watchlist
from pipeline.models import NewsItem
from pipeline.radar.extract import ItemTags
from pipeline.radar.signals import Signal

log = logging.getLogger(__name__)
STATE_PATH = ROOT / "data" / "radar_state.json"

# Names that are organisations but never "new entrants" (press, platforms, generic terms).
NOISE = {"google", "microsoft", "amazon", "apple", "meta", "github", "hugging face", "reuters", "bloomberg",
         "techcrunch", "the information", "wall street journal", "financial times", "cnbc", "youtube", "x",
         "twitter", "linkedin", "reddit", "openai", "anthropic", "nvidia", "amd", "intel", "european union", "eu",
         "white house", "u.s.", "us", "china", "uae", "saudi arabia", "ai", "llm"}


def norm(name: str) -> str:
    """Key for comparing names across sources: 'Reflection AI', 'reflectionai' and 'Reflection Labs' all → 'reflection'."""
    n = re.sub(r"[^\w\s]", "", name.lower())
    n = re.sub(r"\b(inc|llc|ltd|corp|corporation|ai|labs?|technologies|the)\b", " ", n)
    n = re.sub(r"\s+", "", n)
    return n[:-2] if n.endswith("ai") and len(n) > 5 else n   # 'reflectionai' (HF org spelling) → 'reflection'


@dataclass
class Candidate:
    name: str
    track: str = "other"
    region: str = "unknown"
    sources: set[str] = field(default_factory=set)      # distinct publishers / feeds
    item_ids: list[str] = field(default_factory=list)
    signals: list[Signal] = field(default_factory=list)
    events: set[str] = field(default_factory=set)

    @property
    def signal_strength(self) -> float:
        return max((s.strength for s in self.signals), default=0.0)

    @property
    def score(self) -> float:
        return round(len(self.sources) + 2 * self.signal_strength + 0.5 * len(self.signals), 2)

    def clears(self, min_sources: int, min_signals: int) -> bool:
        return len(self.sources) >= min_sources and len(self.signals) >= min_signals


def build_candidates(items: list[NewsItem], tags: dict[str, ItemTags], signals: list[Signal],
                     watch: Watchlist) -> dict[str, Candidate]:
    known = {norm(t) for e in watch.entities for t in e.terms}
    noise = {norm(n) for n in NOISE}
    cands: dict[str, Candidate] = {}
    by_id = {i.id: i for i in items}

    for item_id, t in tags.items():
        item = by_id.get(item_id)
        if not item:
            continue
        for m in t.mentions:
            if m.role != "subject" or m.kind == "person":
                continue
            key = norm(m.name)
            if not key or key in known or key in noise or len(key) < 3:
                continue
            c = cands.setdefault(key, Candidate(name=m.name, track=m.track))
            c.sources.add(item.source)
            c.item_ids.append(item.id)
            c.events.add(t.event)
            if t.region != "unknown":
                c.region = t.region

    for s in signals:
        key = norm(s.name)
        if not key or key in known or key in noise or len(key) < 3:
            continue
        c = cands.setdefault(key, Candidate(name=s.name, track=s.track_hint or "other"))
        c.signals.append(s)
    return cands


def load_state() -> dict[str, Any]:
    return json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def update_state(state: dict[str, Any], cands: dict[str, Candidate], week: str) -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    for key, c in cands.items():
        rec = state.setdefault(key, {"name": c.name, "first_seen": today, "status": "candidate", "weeks": {}})
        rec["weeks"][week] = {"sources": len(c.sources), "signals": len(c.signals), "score": c.score, "track": c.track}


def surface(cands: dict[str, Candidate], state: dict[str, Any], cfg: dict[str, Any], week: str) -> list[NewsItem]:
    """Turn the candidates that clear the bar into NewsItems (track='radar') the editor can pick."""
    r = cfg.get("radar", {})
    out: list[NewsItem] = []
    ranked = sorted(cands.values(), key=lambda c: c.score, reverse=True)
    for c in ranked:
        rec = state.get(norm(c.name), {})
        if rec.get("status") == "ignored" or not c.clears(r.get("min_sources", 2), r.get("min_signals", 1)):
            continue
        weeks_seen = len(rec.get("weeks", {}))
        evidence = [f"- {s.note}: {s.url}" for s in c.signals[:4]]
        out.append(NewsItem(
            source="Radar", source_type="rss",
            title=f"Radar: {c.name} — new name in {c.track} ({len(c.sources)} sources, {len(c.signals)} signals)",
            summary=(f"{c.name} is not on the watchlist but was the subject of {len(c.sources)} independent reports this week "
                     f"({', '.join(sorted(c.events))}) and shows hard signals:\n" + "\n".join(evidence) +
                     f"\nSeen in {weeks_seen} week(s). Source items: {', '.join(c.item_ids[:6])}."),
            url=c.signals[0].url if c.signals else f"radar://{norm(c.name)}",
            published=datetime.now(timezone.utc), source_weight=1.0,
            track="radar", region=c.region, entities=[c.name],
        ))
        if len(out) >= r.get("max_surfaced", 3):
            break
    log.info("Radar: %d candidates, %d surfaced", len(cands), len(out))
    return out


def report_md(cands: dict[str, Candidate], state: dict[str, Any], cfg: dict[str, Any]) -> str:
    """Markdown for the weekly review issue: promote / ignore by editing data/radar_state.json."""
    r = cfg.get("radar", {})
    rows = sorted(cands.values(), key=lambda c: c.score, reverse=True)[:15]
    lines = ["## رادار الأسبوع · radar candidates", "",
             "| name | track | sources | signals | score | weeks seen | clears bar |", "|---|---|---|---|---|---|---|"]
    for c in rows:
        rec = state.get(norm(c.name), {})
        lines.append(f"| {c.name} | {c.track} | {len(c.sources)} | {len(c.signals)} | {c.score} | "
                     f"{len(rec.get('weeks', {}))} | {'yes' if c.clears(r.get('min_sources', 2), r.get('min_signals', 1)) else ''} |")
    lines += ["", "To promote a name, add it to `config/watchlist.yaml`; to silence one, set its `status` to `ignored` in `data/radar_state.json`."]
    return "\n".join(lines)


def run_radar(items: list[NewsItem], watch: Watchlist, cfg: dict[str, Any], week: str,
              out_dir: Path | None = None) -> list[NewsItem]:
    """Full radar pass. Extraction needs ANTHROPIC_API_KEY; without it only hard signals run."""
    from pipeline.radar.extract import extract
    from pipeline.radar.signals import collect_signals

    if not cfg.get("radar", {}).get("enabled", True):
        return []
    try:
        tags = extract(items, cache_path=(out_dir / "radar_tags.json") if out_dir else None)
    except Exception as exc:  # noqa: BLE001 — no key / API down: the radar degrades, the run continues
        log.warning("Radar extraction skipped: %s", exc)
        tags = {}
    signals = collect_signals(cfg)
    cands = build_candidates(items, tags, signals, watch)
    state = load_state()
    update_state(state, cands, week)
    save_state(state)
    if out_dir:
        (out_dir / "radar_report.md").write_text(report_md(cands, state, cfg), encoding="utf-8")
    return surface(cands, state, cfg, week)
