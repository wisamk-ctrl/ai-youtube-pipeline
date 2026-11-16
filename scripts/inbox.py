"""The daily comment inbox (pipeline/publish/inbox.py).

    python scripts/inbox.py daily            collect, sort, draft, open today's "Inbox" issue
    python scripts/inbox.py act              apply the founder's commands (env COMMANDS, ISSUE)
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.publish import inbox  # noqa: E402

STATE = ROOT / "data" / "inbox.json"
NOW = datetime.now(timezone.utc)


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def daily(cfg: dict) -> None:
    ic = cfg.get("inbox", {})
    state = inbox.load(STATE)
    fetched, unread = [], []
    srcs = inbox.sources()
    for name, src in srcs.items():
        try:
            fetched += src.comments()
        except Exception as exc:  # noqa: BLE001 — one platform failing must not hide the others
            unread.append(f"{name.capitalize()}: {exc}")
    new = inbox.collect(state, fetched, NOW)
    labels = {}
    if new:
        import anthropic
        try:
            labels = inbox.sort_comments(new[: int(ic.get("max_per_day", 80))], ic.get("model", "claude-opus-5-5"),
                                         anthropic.Anthropic(max_retries=3))
        except Exception as exc:  # noqa: BLE001 — unsorted comments still reach the founder
            unread.append(f"Sorting failed, comments listed unsorted: {exc}")
    inbox.apply_sort(new, labels)
    repliers = {k: v.reply for k, v in srcs.items()}
    thanked = inbox.thank(new, ic.get("thanks", []), repliers, int(ic.get("thanks_per_day", 20))) \
        if ic.get("auto_thanks") else []
    lessons = inbox.count_themes(state, new, int(ic.get("recurring_after", 3)), NOW)
    inbox.log_lessons(ROOT / "docs" / "LESSONS.md", lessons)
    queue = json.loads((ROOT / "data" / "social_queue.json").read_text(encoding="utf-8")) \
        if (ROOT / "data" / "social_queue.json").exists() else []
    hand = inbox.by_hand(queue, NOW, int(ic.get("by_hand_days", 3)))
    waiting = [c for c in state["comments"].values() if c.get("status") == "awaiting"]
    inbox.save(STATE, state, now=NOW)
    print(f"{len(fetched)} fetched, {len(new)} new, {len(waiting)} awaiting, {len(hand)} by hand, {len(unread)} unread")
    if not (new or hand or unread):
        return
    body = inbox.digest(new, waiting, hand, lessons, thanked, unread, NOW)
    if os.environ.get("GITHUB_REPOSITORY"):
        gh("issue", "create", "--repo", os.environ["GITHUB_REPOSITORY"], "--title", f"Inbox: {NOW:%a %d %b}",
           "--body", body)
    else:
        print(body)


def act() -> None:
    state = inbox.load(STATE)
    commands = inbox.parse_commands(os.environ.get("COMMANDS", ""))
    if not commands:
        print("No command found.")
        return
    lines = inbox.act(state, commands, {k: v.reply for k, v in inbox.sources().items()}, NOW)
    inbox.save(STATE, state, now=NOW)
    print("\n".join(lines))
    if os.environ.get("GITHUB_REPOSITORY") and os.environ.get("ISSUE"):
        gh("issue", "comment", os.environ["ISSUE"], "--repo", os.environ["GITHUB_REPOSITORY"], "--body", "\n".join(lines))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cfg = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))
    {"daily": lambda: daily(cfg), "act": act}[sys.argv[1]]()
