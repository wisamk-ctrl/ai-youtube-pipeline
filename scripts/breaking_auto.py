"""Should a rendered breaking Short post on its own, without the founder's `post <week>`? (founder 2026-11-25)

The founder asked for breaking Shorts to go out as soon as the news lands, unless the pipeline is not sure,
as a test until `breaking.auto_post_until`. "Sure" means the script already passed its figure and source
checks (no draft exists otherwise) and the finished video passed scripts/short_check.py with nothing flagged.
Explainer Shorts still wait for the founder.

    python scripts/breaking_auto.py <week> "<short_check report>"   → exit 0 = post now, 1 = hold; prints why"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PASSED = "✅ **Automatic check passed**"


def decide(week: str, qc: str, settings: dict, now: datetime | None = None) -> tuple[bool, str]:
    now = now or datetime.now(timezone.utc)
    until = (settings.get("breaking") or {}).get("auto_post_until")
    if not until:
        return False, "auto-posting is off: waiting for your `post`"
    end = until if isinstance(until, datetime) else datetime.fromisoformat(str(until))
    if now >= end:
        return False, f"the auto-post test ended {end:%a %d %b %H:%M}: waiting for your `post`"
    if "-brk-" not in week:
        return False, "only breaking Shorts post on their own: waiting for your `post`"
    if not qc.strip().startswith(PASSED):
        flagged = "\n".join(ln for ln in qc.splitlines() if ln.startswith("- ")) or "no automatic check result"
        return False, f"not sure, so held for you:\n{flagged}"
    return True, f"posting now on its own (your test until {end:%a %d %b %H:%M})"


if __name__ == "__main__":
    s = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8")) or {}
    ok, why = decide(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "", s)
    print(why)
    sys.exit(0 if ok else 1)
