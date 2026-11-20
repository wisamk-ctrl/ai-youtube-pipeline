"""The news watch: a light collection every few hours, so a story that breaks on a Wednesday is kept
and the founder hears about the big ones the same day (W46-en: the Microsoft 365 outage of 12 November
was never collected; until then news was read once a week, on Saturday morning).

State lives in data/news_watch.json: every item seen in the last `keep_days`, with when it was first
seen and whether it was flagged. The weekly collection adds these items to its own, so a story that has
left the search results by Saturday still reaches the planner."""
from __future__ import annotations

import copy
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from pipeline.models import NewsItem

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "data" / "news_watch.json"


def load(path: Path = STATE) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"items": {}, "runs": []}


def save(state: dict[str, Any], path: Path = STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def _norm(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", title.lower()).strip()


def clusters(items: list[NewsItem], similarity: float = 0.6) -> list[list[NewsItem]]:
    """Items that tell the same story, by headline."""
    out: list[list[NewsItem]] = []
    for i in items:
        home = next((c for c in out if SequenceMatcher(None, _norm(i.title), _norm(c[0].title)).ratio() >= similarity), None)
        home.append(i) if home else out.append([i])
    return out


def collect(cfg: dict[str, Any]) -> tuple[list[NewsItem], set[str]]:
    """(everything found, ids that came from the always-flag searches)."""
    from pipeline.ingestion import watch_sources
    from pipeline.ingestion.rss_ingest import fetch_all_feeds
    from pipeline.ingestion.watchlist import load_watchlist
    nw = cfg.get("news_watch", {})
    c = copy.deepcopy(cfg)
    c["ingestion"]["lookback_days"] = int(nw.get("lookback_days", 2))
    c["ingestion"].setdefault("watchlist", {}).setdefault("fetch_articles", {})["max_items"] = int(nw.get("article_fetches", 25))
    c["ingestion"]["watchlist"]["pause_seconds"] = float(nw.get("pause_seconds", 1.5))
    sites = c["ingestion"].get("google_news_sites") or []
    urgent_cfg = copy.deepcopy(c)
    urgent_cfg["ingestion"]["google_news_sites"] = [s for s in sites if s.get("raw")]
    rest_cfg = copy.deepcopy(c)
    rest_cfg["ingestion"]["google_news_sites"] = [s for s in sites if not s.get("raw")]
    watch = load_watchlist()
    urgent = watch_sources.fetch_site_queries(urgent_cfg)
    found = list(urgent)
    for name, fetch in (("regional sites", lambda: watch_sources.fetch_site_queries(rest_cfg)),
                        ("watched names", lambda: watch_sources.fetch_google_news(watch, c)),
                        ("feeds", lambda: fetch_all_feeds(c))):
        try:
            found += fetch()
        except Exception as exc:  # noqa: BLE001 — one source failing must not lose the others
            log.warning("News watch: %s failed: %s", name, exc)
    for i in found:
        watch.tag(i)
    return found, {i.id for i in urgent}


def update(state: dict[str, Any], found: list[NewsItem], urgent: set[str], cfg: dict[str, Any],
           now: datetime) -> list[dict[str, Any]]:
    """Record what is new; return the stories to tell the founder about now: anything from an always-flag
    search, and any story at least `min_publishers` different outlets are carrying."""
    nw = cfg.get("news_watch", {})
    known = state.setdefault("items", {})
    new = [i for i in found if i.id not in known]
    for i in new:
        known[i.id] = {**i.to_dict(), "first_seen": now.isoformat(timespec="minutes"), "flagged": False}
    cutoff = now - timedelta(days=int(nw.get("keep_days", 10)))
    for k in [k for k, v in known.items() if datetime.fromisoformat(v["first_seen"]) < cutoff]:
        del known[k]
    recent = [NewsItem.from_dict({k: v for k, v in d.items() if k not in ("first_seen", "flagged")}) for d in known.values()]
    flagged: list[dict[str, Any]] = []
    need = int(nw.get("min_publishers", 4))
    for group in clusters(recent):
        outlets = sorted({i.source for i in group})
        if any(known[i.id]["flagged"] for i in group):      # already told once: a story is announced one time
            for i in group:
                known[i.id]["flagged"] = True
            continue
        if not (len(outlets) >= need or any(i.id in urgent for i in group)):
            continue
        lead = max(group, key=lambda i: len(i.summary))
        flagged.append({"title": lead.title, "url": lead.url, "outlets": outlets,
                        "region": next((i.region for i in group if i.region), ""),
                        "why": "outage search" if any(i.id in urgent for i in group) else f"{len(outlets)} outlets"})
        for i in group:
            known[i.id]["flagged"] = True
    state.setdefault("runs", []).append({"at": now.isoformat(timespec="minutes"), "found": len(found), "new": len(new),
                                         "flagged": len(flagged)})
    state["runs"] = state["runs"][-60:]
    return flagged


def digest(flagged: list[dict[str, Any]], now: datetime) -> str:
    lines = [f"**News watch, {now:%a %d %b %H:%M} UTC**", ""]
    for f in flagged:
        where = f" · {f['region']}" if f["region"] else ""
        lines.append(f"- [{f['title']}]({f['url']}) ({f['why']}{where}): {', '.join(f['outlets'][:6])}")
    lines += ["", "These are kept for this week's episode. Reply here if one should lead it or go out as a Short sooner."]
    return "\n".join(lines)


def flagged_ids(since: datetime, path: Path = STATE) -> set[str]:
    """Ids of the items in stories the watch flagged as big since `since`: each such story gets a seat in the weekly."""
    return {k for k, d in load(path).get("items", {}).items()
            if d.get("flagged") and NewsItem.from_dict({k2: v for k2, v in d.items()
                                                        if k2 not in ("first_seen", "flagged")}).published >= since}


def kept_items(since: datetime, path: Path = STATE) -> list[NewsItem]:
    """What the watch has kept since `since`, for the weekly collection."""
    out = []
    for d in load(path).get("items", {}).values():
        item = NewsItem.from_dict({k: v for k, v in d.items() if k not in ("first_seen", "flagged")})
        if item.published >= since:
            out.append(item)
    return out
