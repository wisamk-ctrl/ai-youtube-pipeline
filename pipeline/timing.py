"""Per-stage wall-clock timing for the render (2026-11-21: the W47-en render took 65 min; measure first).

`TIMER.stage("name")` logs each stage's seconds as it ends; `TIMER.write(out / "timings.json")` keeps the
whole table with the week, and `TIMER.table()` prints it as Markdown for the run summary."""
from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from pathlib import Path

log = logging.getLogger(__name__)


def _clock(s: float) -> str:
    return f"{int(s) // 60}:{int(s) % 60:02d}"


class Timer:
    def __init__(self) -> None:
        self.seconds: dict[str, float] = {}
        self.details: dict[str, float] = {}     # parts of a stage: shown, not added to the total
        self.started = time.monotonic()

    @contextmanager
    def stage(self, name: str):
        t0 = time.monotonic()
        try:
            yield
        finally:
            took = time.monotonic() - t0
            self.seconds[name] = self.seconds.get(name, 0.0) + took
            log.info("⏱ %s: %.1f s", name, took)

    def add_detail(self, name: str, seconds: float) -> None:
        self.details[name] = self.details.get(name, 0.0) + seconds

    @contextmanager
    def detail(self, name: str):
        t0 = time.monotonic()
        try:
            yield
        finally:
            self.add_detail(name, time.monotonic() - t0)

    def total(self) -> float:
        return sum(self.seconds.values())

    def table(self) -> str:
        rows = ["| Stage | Time |", "|---|---|"]
        rows += [f"| {k} | {v:.0f} s ({_clock(v)}) |" for k, v in self.seconds.items()]
        rows += [f"| ↳ {k} | {v:.0f} s ({_clock(v)}) |" for k, v in self.details.items()]
        rows.append(f"| **total** | **{self.total():.0f} s ({_clock(self.total())})** |")
        return "\n".join(rows)

    def write(self, dest: Path) -> Path:
        dest = Path(dest)
        dest.write_text(json.dumps({"stages": [{"stage": k, "seconds": round(v, 2)} for k, v in self.seconds.items()],
                                    "details": [{"stage": k, "seconds": round(v, 2)} for k, v in self.details.items()],
                                    "total_s": round(self.total(), 2)}, indent=2), encoding="utf-8")
        log.info("Render timings → %s\n%s", dest, self.table())
        return dest


TIMER = Timer()
