"""Stories already covered (founder 2026-11-20: "not repeat news from previous episodes unless there's something
new substantially"). data/covered.json keeps, per week, the headlines of the items the episode's plan used. The
next weeks' ranking marks those stories down and the editor sees them, to include one again only for real news."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "data" / "covered.json"


def _key(week: str) -> tuple[int, int]:
    m = re.match(r"(\d{4})-W(\d{2})", week)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def record(path: Path, week: str, titles: list[str]) -> None:
    base = re.match(r"\d{4}-W\d{2}", week)
    if not base:                                  # breaking Shorts and test folders are not episodes
        return
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data[base.group(0)] = list(dict.fromkeys(titles))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=1), encoding="utf-8")


def recent(path: Path, week: str, weeks: int = 4) -> list[str]:
    """Headlines covered in the `weeks` episodes before `week` (never `week` itself)."""
    if not path.exists():
        return []
    now = _key(week)
    data = json.loads(path.read_text(encoding="utf-8"))
    past = sorted((k for k in data if _key(k) < now), key=_key)[-weeks:]
    return [t for k in past for t in data[k]]
