"""Draft the explainer Shorts of an approved ranking (pipeline/explainer.py; workflow explainer).

    python scripts/explainer.py <week>     # data/ranking/<week>.json → reviewed/<date>-exp-<slug>-en/ folders
    python scripts/explainer.py --dry      # a ranking built now from the news watch; prints the scripts, keeps nothing

Prints EXPLAINERS=<folder names, space separated> on the last line. Needs ANTHROPIC_API_KEY."""
from __future__ import annotations

import logging
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def dry_ranking(cfg: dict) -> dict:
    from pipeline.ingestion import covered as cov
    from pipeline.ingestion import news_watch
    from pipeline.ingestion.scoring import score_item
    from pipeline.ranking import rank
    from pipeline.ranking.cluster import cluster
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=7)
    done = cov.recent(cov.STATE, "dry-run")
    stories = cluster([score_item(i, now) for i in news_watch.kept_items(since)], cfg,
                      flagged=news_watch.flagged_ids(since), covered=done)
    return rank.build(stories, cfg, "dry-run", covered=done)


def main(arg: str) -> int:
    import anthropic
    from pipeline import explainer
    from pipeline.config import load_settings
    from pipeline.ranking import rank
    cfg, client = load_settings(), anthropic.Anthropic(max_retries=4)
    if arg == "--dry":
        r = dry_ranking(cfg)
        print("## Shorts candidates in this ranking")
        for s in r.get("shorts", []):
            print(f"- {s['job']}: {s['title']}\n  - fact: {s['fact']}\n  - idea: {s['implication']}\n  - question: {s['question']}")
        with tempfile.TemporaryDirectory() as tmp:
            made = explainer.run(cfg, r, client, done_path=Path(tmp) / "done.json", root=Path(tmp))
            for week in made:
                f = Path(tmp) / "reviewed" / week
                print(f"\n## {week}\n\n```\n{(f / 'script.md').read_text(encoding='utf-8')}\n```\n\n"
                      f"### Each line and its source\n{(f / 'sources_ok.txt').read_text(encoding='utf-8')}")
        print(f"\nDry run: {len(made)} explainer Short(s) passed every check; nothing was saved.")
        return 0
    r = rank.load(arg)
    if not r:
        sys.exit(f"no ranking saved for {arg}")
    if not r.get("approved"):
        sys.exit(f"the {arg} ranking is not approved yet")
    print("EXPLAINERS=" + " ".join(explainer.run(cfg, r, client)))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main(sys.argv[1]) if len(sys.argv) == 2 else print(__doc__) or 2)
