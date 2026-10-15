"""
Token meter: every Claude call records its usage here, the run writes usage.json, and the
review issue shows tokens per model plus a cost when `pricing` is filled in settings.yaml.

Prices are NOT hard-coded: they change, and a wrong number is worse than none. Fill
`pricing.<model>.input` / `.output` (USD per million tokens) from anthropic.com/pricing;
until then the meter reports tokens only.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_calls: list[dict[str, Any]] = []


def record(step: str, model: str, usage: Any) -> None:
    """usage is the SDK's Usage object (input_tokens / output_tokens, plus cache fields when present)."""
    if usage is None:
        return
    g = lambda k: int(getattr(usage, k, 0) or 0)  # noqa: E731
    _calls.append({"step": step, "model": model, "input": g("input_tokens"), "output": g("output_tokens"),
                   "cache_read": g("cache_read_input_tokens"), "cache_write": g("cache_creation_input_tokens")})


def reset() -> None:
    _calls.clear()


def summary(pricing: dict[str, Any] | None = None) -> dict[str, Any]:
    per_model: dict[str, dict[str, int]] = defaultdict(lambda: {"calls": 0, "input": 0, "output": 0})
    for c in _calls:
        m = per_model[c["model"]]
        m["calls"] += 1
        m["input"] += c["input"] + c["cache_read"] + c["cache_write"]
        m["output"] += c["output"]
    out: dict[str, Any] = {"models": dict(per_model), "calls": list(_calls)}
    cost, priced = 0.0, True
    for model, m in per_model.items():
        p = (pricing or {}).get(model)
        if not p or p.get("input") is None or p.get("output") is None:
            priced = False
            continue
        cost += m["input"] / 1e6 * float(p["input"]) + m["output"] / 1e6 * float(p["output"])
    out["cost_usd"] = round(cost, 2) if priced and per_model else None
    return out


def write(out_dir: Path, pricing: dict[str, Any] | None = None) -> dict[str, Any]:
    s = summary(pricing)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "usage.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    line = " · ".join(f"{m}: {v['calls']} calls, {v['input']:,} in / {v['output']:,} out" for m, v in s["models"].items())
    log.info("Usage: %s%s", line or "no model calls", f" · ≈ ${s['cost_usd']}" if s["cost_usd"] is not None else " (set pricing in settings.yaml for a cost)")
    return s
