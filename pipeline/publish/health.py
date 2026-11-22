"""Daily health check (founder 2026-11-23): a silent failure must never look like a quiet day.

Every run was green while nothing told the founder about a refused sign-in, a post dropped after its retries or a
news watch that had stopped. These checks ask "did the last SUCCESS happen, and for the right account", never "did
it run". Pure functions; scripts/health.py does the reading, the issue and the WhatsApp message.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_BROKEN = ("refused", "not usable", "NOT the show's channel", "no Page connected")


def _when(text: str) -> datetime:
    d = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def queue_problems(queue: list[dict[str, Any]], now: datetime, stuck_hours: float = 3, days: int = 14) -> list[str]:
    """Posts that failed, may be live but are unconfirmed, were given up on, or are approved and due yet unsent."""
    out = []
    for e in queue:
        due = _when(e["due"])
        if due < now - timedelta(days=days) or due > now:
            continue
        for p, r in e.get("posts", {}).items():
            s, err, tag = r.get("status"), r.get("error", ""), f"{e['id']} on {p}"
            if s == "failed":
                out.append(f"{tag}: failed, will retry ({err})")
            elif s == "unconfirmed":
                out.append(f"{tag}: may already be live and was not sent again; check it by hand ({err})")
            elif s == "skipped" and err and not r.get("note"):
                out.append(f"{tag}: gave up after {r.get('attempts', '?')} tries ({err})")
            elif s == "queued" and e.get("approved") and due < now - timedelta(hours=stuck_hours):
                out.append(f"{tag}: approved and due since {e['due']}, still waiting")
    return out


def ingest_problems(runs: list[dict[str, Any]], now: datetime, max_age_hours: float = 8, empty_runs: int = 3) -> list[str]:
    """The news watch (data/news_watch.json → runs): its last run is recent and the sources still return items."""
    if not runs:
        return ["The news watch has no recorded run"]
    last = runs[-1]
    if _when(last["at"]) < now - timedelta(hours=max_age_hours):
        return [f"The news watch last ran at {last['at']} (expected every two hours)"]
    tail = runs[-empty_runs:]
    if len(tail) == empty_runs and all(not r.get("found") for r in tail):
        return [f"The news watch found nothing in its last {empty_runs} runs: the sources may be failing"]
    return []


def workflow_problems(last_success: dict[str, str | None], now: datetime, max_age_hours: dict[str, float]) -> list[str]:
    """Each scheduled workflow's last SUCCESSFUL run is recent enough (GitHub also switches schedules off quietly)."""
    out = []
    for name, hours in max_age_hours.items():
        at = last_success.get(name)
        if not at:
            out.append(f"{name}: never succeeded in the runs GitHub keeps")
        elif _when(at) < now - timedelta(hours=hours):
            out.append(f"{name}: last success {at}, more than {hours:g} hours ago")
    return out


def scheduled_workflows(folder: Path) -> dict[str, str]:
    """Workflow name → file name, for every workflow that runs on a schedule."""
    import yaml
    out = {}
    for f in sorted(folder.glob("*.yml")):
        doc = yaml.safe_load(f.read_text(encoding="utf-8"))
        on = doc.get(True, doc.get("on", {}))                                   # PyYAML reads the key `on` as True
        if isinstance(on, dict) and "schedule" in on:
            out[doc["name"]] = f.name
    return out


def _lines(report: str) -> dict[str, str]:
    out = {}
    for line in report.splitlines():
        if line.startswith("- ") and ":" in line:
            label, _, text = line[2:].partition(":")
            out[label.strip()] = text.strip()
    return out


def identities(report: str) -> dict[str, list[str]]:
    """Who each connection reaches (the bold names in scripts/connect.py's report), per connection."""
    return {label: _BOLD.findall(text) for label, text in _lines(report).items() if _BOLD.search(text)}


def connection_problems(report: str, baseline: dict[str, list[str]]) -> list[str]:
    """A refused or unusable sign-in, a connection reaching a different account than last time, or one now gone."""
    out, lines, now = [], _lines(report), identities(report)
    for label, text in lines.items():
        if any(b in text for b in _BROKEN):
            out.append(f"{label}: {text}")
        elif label in baseline and label in now and now[label] != baseline[label]:
            out.append(f"{label}: now reaches {', '.join(now[label])}, was {', '.join(baseline[label])}")
        elif label in baseline and label not in now:
            out.append(f"{label}: no longer connected (was {', '.join(baseline[label])})")
    out += [f"{label}: missing from the check (was {', '.join(was)})" for label, was in baseline.items() if label not in lines]
    return out


def report(problems: dict[str, list[str]]) -> str:
    parts = [f"### {area}\n" + "\n".join(f"- {p}" for p in items) for area, items in problems.items() if items]
    return "\n\n".join(parts) + "\n" if parts else "All clear: connections, posting queue, news watch and scheduled jobs.\n"
