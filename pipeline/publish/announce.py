"""The episode's announcement on LinkedIn and the Facebook Page, once it is public (run_pipeline.py phase announce).

2026-11-23: a run that posted to LinkedIn and then failed on Facebook kept no record, so running it again would have
posted the episode to LinkedIn twice; an empty announcement text posted nowhere and said nothing. Each channel is
posted once and written to data/announced.json; whatever did not go out is returned as a problem, and the phase
fails on it so the run is reported.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable


def announce(text: str, done: dict[str, str], posters: dict[str, Callable[[], str]]) -> tuple[dict[str, str], list[str]]:
    """Post on every channel in `posters` not yet in `done`. Returns the updated record and what did not go out."""
    done, todo = dict(done), [c for c in posters if not done.get(c)]
    if todo and not text.strip():
        return done, [f"no announcement text (plan.json → linkedin_post_en is empty): nothing posted to {', '.join(todo)}"]
    problems = []
    for channel in todo:
        try:
            done[channel] = str(posters[channel]() or "posted")
        except Exception as exc:  # noqa: BLE001 — one channel must not stop the other, and must not go unreported
            problems.append(f"{channel}: not posted ({exc})")
    return done, problems


def load(path: Path, week: str) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8")).get(week, {}) if path.exists() else {}


def save(path: Path, week: str, done: dict[str, str]) -> None:
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    data[week] = done
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
