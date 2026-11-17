"""Run the news watch once (pipeline/ingestion/news_watch.py) and tell the founder about big stories."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.ingestion import news_watch  # noqa: E402

TITLE = "News watch"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cfg = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    state = news_watch.load()
    first_run = not state.get("items")
    found, urgent = news_watch.collect(cfg)
    flagged = news_watch.update(state, found, urgent, cfg, now)
    news_watch.save(state)
    print(f"{len(found)} found, {state['runs'][-1]['new']} new, {len(flagged)} flagged")
    if not flagged or not os.environ.get("GITHUB_REPOSITORY"):
        print(news_watch.digest(flagged, now) if flagged else "Nothing to flag.")
        sys.exit(0)
    repo = os.environ["GITHUB_REPOSITORY"]
    body = news_watch.digest(flagged[:12], now) + ("\n\n(First run: this is the backlog of the last two days.)" if first_run else "")
    num = subprocess.run(["gh", "issue", "list", "--repo", repo, "--state", "open", "--search", f'"{TITLE}" in:title',
                          "--json", "number,title", "--jq", f'[.[] | select(.title == "{TITLE}")][0].number'],
                         capture_output=True, text=True).stdout.strip()
    if num and num != "null":
        subprocess.run(["gh", "issue", "comment", num, "--repo", repo, "--body", body], check=True)
    else:
        subprocess.run(["gh", "issue", "create", "--repo", repo, "--title", TITLE, "--body", body], check=True)
