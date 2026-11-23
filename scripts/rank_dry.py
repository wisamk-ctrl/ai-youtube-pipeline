"""A ranking dry run on the news watch's last seven days (workflow rank-dry): group, judge, join, slot, and print.
Nothing is saved, no issue is opened and no decision is recorded. It calls the ranking judge once (a few cents).
The real ranking reads the week's ingest pool, so its list can differ from this one."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    from pipeline.config import load_settings
    from pipeline.ingestion import covered as cov
    from pipeline.ingestion import news_watch
    from pipeline.ingestion.scoring import score_item
    from pipeline.ranking import rank
    from pipeline.ranking.cluster import cluster
    from pipeline.ranking.judge import FALLBACK
    cfg, now = load_settings(), datetime.now(timezone.utc)
    since = now - timedelta(days=7)
    items = [score_item(i, now) for i in news_watch.kept_items(since)]
    done = cov.recent(cov.STATE, "dry-run")
    stories = cluster(items, cfg, flagged=news_watch.flagged_ids(since), covered=done)
    before = [(s["id"], s["title"]) for s in stories]
    r = rank.build(stories, cfg, "dry-run", covered=done)
    print(f"## Dry run: {len(items)} items → {len(before)} stories → {len(r['stories'])} after joining · judge: {r['judge']}\n")
    print("### Joined by the judge")
    joined = [s for s in r["stories"] if s.get("merged")]
    for s in joined:
        print(f"- **{s['title']}** ({s['outlet_count']} outlets) now also holds:")
        for t in s["merged"]:
            print(f"  - {t}")
    if not joined:
        print("- nothing")
    print("\n### Stories before joining")
    for sid, title in before:
        print(f"- {sid}: {title}")
    print("\n### The ranking\n")
    print(rank.to_md(r, cfg))
    return 1 if r["judge"] == FALLBACK else 0     # the fallback means the model call failed: not a test of the judge


if __name__ == "__main__":
    sys.exit(main())
