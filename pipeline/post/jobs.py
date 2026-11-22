"""Independent ffmpeg jobs run side by side (2026-11-21: the edit's 162 segments and the 3 Shorts were
encoded one at a time on a 4-CPU runner)."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def workers(cfg: dict[str, Any] | None) -> int:
    """post.workers: parallel jobs; 0 = one per CPU. Default 4 (the hosted runner's CPU count)."""
    n = int(((cfg or {}).get("post", {}) or {}).get("workers", 4))
    return n if n > 0 else (os.cpu_count() or 2)


def run_all(fns: list[Callable[[], T]], workers: int) -> list[T]:
    """Each job's result, in the order given. The first job to fail raises its error after the rest finish."""
    if workers <= 1 or len(fns) <= 1:
        return [f() for f in fns]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(f) for f in fns]
    return [f.result() for f in futures]
