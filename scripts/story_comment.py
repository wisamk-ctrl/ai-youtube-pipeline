#!/usr/bin/env python3
"""
Apply a `/story …` comment on the weekly "Ranking: <week>" issue to data/ranking/<week>.json.

    /story s1a2 deep because the Jordan angle matters to our viewers
    /story s1a2 drop because we covered it in Thursday's breaking Short
    /story s1a2 auto because changed my mind          (hands the story back to the ranking)
    /story approve                                    (writes the script from the list as it stands)

Slots: deep, quick, radar, short. Every move needs a reason, and it is logged in the ranking file with who and
when. Used by .github/workflows/story-decide.yml (repository owner only). The comment arrives in the BODY
environment variable and never passes through a shell; the results go to $GITHUB_OUTPUT in random-delimiter
heredocs (scripts/radar_comment.py), so a multi-line reason cannot add outputs of its own.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.config import load_settings  # noqa: E402
from pipeline.ranking import rank  # noqa: E402
from radar_comment import write_outputs  # noqa: E402

_LINE = re.compile(r"^/story\s+(\S+?)\s+(deep|quick|radar|short|drop|auto)\s*(?:\bbecause\b|:|—|-)\s*(\S.*)$", re.I)


def parse(body: str) -> tuple[str, str, str]:
    """(story id, action, reason) from the comment's first line; ("", "approve", "") for an approval."""
    line = (body or "").strip().splitlines()[0].strip() if (body or "").strip() else ""
    if re.fullmatch(r"/story\s+approve", line, re.I):
        return "", "approve", ""
    m = _LINE.match(line)
    if not m:
        raise ValueError("use `/story <id> <deep|quick|radar|short|drop|auto> because <reason>` or `/story approve`")
    return m.group(1).lower(), m.group(2).lower(), m.group(3).strip()


def main() -> int:
    week = re.search(r"\b(\d{4}-W\d{2})\b", os.environ.get("TITLE", ""))
    by = os.environ.get("ACTOR", "") or "founder"
    try:
        sid, action, reason = parse(os.environ.get("BODY", ""))
        if not week:
            raise ValueError("no week in the issue title")
        r = rank.load(week.group(1))
        if r is None:
            raise ValueError(f"no ranking saved for {week.group(1)}")
        cfg = load_settings()
        if action == "approve":
            rank.approve(r, by)
            result = f"Approved the {r['week']} ranking. Writing the script from it now; the Review issue follows."
        else:
            rank.decide(r, sid, action, reason, by, cfg)
            result = (f"`{sid}` → **{action}** (logged: {reason}). The list now reads as below; "
                      f"`/story approve` when it is right.\n\n{rank.to_md(r, cfg)}")
    except ValueError as e:
        write_outputs(os.environ.get("GITHUB_OUTPUT"), {"kind": "error", "week": "", "result": f"Not applied: {e}"})
        print(f"::warning::{e}")
        return 0
    rank.save(r)
    write_outputs(os.environ.get("GITHUB_OUTPUT"), {"kind": action if action == "approve" else "decide",
                                                    "week": r["week"], "result": result})
    return 0


if __name__ == "__main__":
    sys.exit(main())
