"""
Coverage report — is the watchlist earning its keep?

After each run, record how many items each watched name produced this week
(`data/coverage.json`), then report:
  * names with no news in the last N weeks (candidates to prune or whose feeds broke),
  * items per track and per region (is the Gulf getting its share? is one track crowding out the rest?).
The Markdown goes into the weekly review issue next to the radar table.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from pipeline.config import ROOT
from pipeline.ingestion.watchlist import Watchlist
from pipeline.models import NewsItem

COVERAGE_PATH = ROOT / "data" / "coverage.json"


def record(items: list[NewsItem], watch: Watchlist, week: str, path: Path = COVERAGE_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    counts = Counter(name for i in items for name in i.entities)
    data[week] = {
        "entities": {e.name: counts.get(e.name, 0) for e in watch.entities},
        "tracks": dict(Counter(i.track or "untagged" for i in items)),
        "regions": dict(Counter(f"{i.track}/{i.region}" for i in items if i.track)),
        "total": len(items),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    return data


def report_md(data: dict[str, Any], watch: Watchlist, week: str, quiet_weeks: int = 4) -> str:
    weeks = sorted(data)[-quiet_weeks:]
    this = data.get(week, {})
    lines = ["## Coverage", ""]
    if this:
        lines.append("**This week by track:** " + ", ".join(f"{t} {n}" for t, n in sorted(this["tracks"].items())))
        lines.append("")
        lines.append("**Models by region:** " + ", ".join(
            f"{r.split('/')[1]} {n}" for r, n in sorted(this["regions"].items()) if r.startswith("models/")) or "none")
        lines.append("")
    if len(weeks) >= quiet_weeks:
        quiet = [e.name for e in watch.entities
                 if all(data[w]["entities"].get(e.name, 0) == 0 for w in weeks)]
        if quiet:
            lines.append(f"**No news in {quiet_weeks} weeks** (prune, or a feed is broken): " + ", ".join(quiet))
        else:
            lines.append(f"Every watched name produced at least one item in the last {quiet_weeks} weeks.")
    else:
        lines.append(f"Quiet-name check starts after {quiet_weeks} weeks of history ({len(weeks)} so far).")
    return "\n".join(lines)
