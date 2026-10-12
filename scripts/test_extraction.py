#!/usr/bin/env python3
"""
Benchmark the local extraction model on the sample week, with no API key.

The watchlist tagger (regex, exact) already knows which watched names each sample item
mentions. The model should find at least those, plus the names we don't know. So:

  recall  = of the watched names the regex found, how many the model also found as mentions
  subject = of the items whose headline names a watched entity, how often the model marks it `subject`
  extra   = names the model found that are NOT on the watchlist (the radar's raw material)

Run on the Mac:  make extract-test       (≈1-3 min on a 7B model for 20 items)
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import ROOT, load_settings  # noqa: E402
from pipeline.ingestion.watchlist import load_watchlist  # noqa: E402
from pipeline.models import NewsItem  # noqa: E402
from pipeline.radar.extract import extract  # noqa: E402
from pipeline.radar.radar import norm  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
cfg = load_settings()
opts = cfg["radar"]["extraction"]
watch = load_watchlist()
items = [watch.tag(NewsItem.from_dict(d)) for d in json.loads((ROOT / "fixtures/sample_week/items.json").read_text(encoding="utf-8"))]

t0 = time.time()
tags = extract(items, cache_path=None, opts=opts)
dt = time.time() - t0
print(f"\n{opts['provider']} / {opts.get('ollama_model') if opts['provider'] == 'ollama' else opts['model']}: "
      f"{len(tags)}/{len(items)} items tagged in {dt:.0f}s ({dt / max(len(items), 1):.1f}s per item)\n")

known_terms = {norm(t): e.name for e in watch.entities for t in e.terms}
hit = total = subj_hit = subj_total = 0
extras: dict[str, int] = {}
for i in items:
    t = tags.get(i.id)
    found = {known_terms.get(norm(m.name)) for m in (t.mentions if t else [])} - {None}
    for name in i.entities:
        total += 1
        hit += name in found
    if i.track and t:
        subj_total += 1
        subj_hit += any(known_terms.get(norm(m.name)) in i.entities and m.role == "subject" for m in t.mentions)
    for m in (t.mentions if t else []):
        if norm(m.name) not in known_terms and m.kind != "person":
            extras[m.name] = extras.get(m.name, 0) + 1
    flag = "" if t else "  ← NOT TAGGED"
    print(f"{(t.event if t else '-'):12} {(t.region if t else '-'):8} {', '.join(sorted(found))[:40]:40} {i.title[:55]}{flag}")

print(f"\nrecall of watched names : {hit}/{total} ({100 * hit / max(total, 1):.0f}%)   target ≥ 85%")
print(f"subject marked correctly: {subj_hit}/{subj_total} ({100 * subj_hit / max(subj_total, 1):.0f}%)   target ≥ 75%")
print(f"unknown names found     : {len(extras)} → " + ", ".join(f"{k} ×{v}" for k, v in sorted(extras.items(), key=lambda kv: -kv[1])[:15]))
print("\nIf recall is low or items are NOT TAGGED, try a larger model (qwen2.5:14b / qwen3:14b) or lower ollama_batch to 4.")
