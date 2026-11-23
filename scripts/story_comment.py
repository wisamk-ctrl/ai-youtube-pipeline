#!/usr/bin/env python3
"""
Apply the founder's comment on the weekly "Ranking: <week>" issue to data/ranking/<week>.json.

    /story 7 deep because the Jordan angle matters to our viewers     (a story's number in the list, or its id)
    /story 3 drop because we covered it in Thursday's breaking Short
    /story 3 auto because changed my mind          (hands the story back to the ranking)
    approve                                        (or `/story approve`: writes the script from the list)

Slots: deep, quick, radar, short. Several commands can go in one comment, one per line; numbers mean the list as
it was shown, whatever an earlier line moved, and if one line cannot be read or names no story, nothing is
applied. Every move needs a reason, and it is logged in the ranking file with who and when. Lines that are not
commands are ignored, so a note can sit beside them.

Used by .github/workflows/story-decide.yml (repository owner only). The comment arrives in the BODY environment
variable and never passes through a shell; the results go to $GITHUB_OUTPUT in random-delimiter heredocs
(scripts/radar_comment.py), so a multi-line reason cannot add outputs of its own. The reply is short (what
moved); the full list is written to $ISSUE_BODY and the workflow replaces the issue's body with it.
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


_APPROVE = re.compile(r"(/story\s+)?approve\W*", re.I)
USAGE = "use `/story <number or id> <deep|quick|radar|short|drop|auto> because <reason>`, or `approve`"


def parse_all(body: str) -> list[tuple[str, str, str]]:
    """Every command in the comment, in order: (story number or id, action, reason); ("", "approve", "") for an
    approval. A line that starts like a command and cannot be read is an error; other lines are notes."""
    out = []
    for line in (body or "").splitlines():
        line = line.strip()
        if _APPROVE.fullmatch(line):
            out.append(("", "approve", ""))
        elif line.lower().startswith("/story"):
            m = _LINE.match(line)
            if not m:
                raise ValueError(f"could not read `{line[:80]}`: {USAGE}")
            out.append((m.group(1).lower(), m.group(2).lower(), m.group(3).strip()))
    if not out:
        raise ValueError(USAGE)
    return out


def parse(body: str) -> tuple[str, str, str]:
    """The comment's first command (kept for callers that take one)."""
    return parse_all(body)[0]


def apply(r: dict, commands: list[tuple[str, str, str]], by: str, cfg: dict, now=None) -> tuple[str, str]:
    """Apply the commands to the ranking → ("approve" | "decide", the short reply). Numbers are looked up in the
    list as it stands before anything moves, and all of them before any is applied."""
    shown = {str(s.get("ref") or n): s["id"] for n, s in enumerate(r["stories"], 1)}
    moves = []
    for ref, action, reason in commands:
        if action == "approve":
            continue
        sid = shown.get(ref) or rank.find(r, ref)["id"]      # find() raises ValueError for an unknown id
        if action not in rank.ACTIONS:
            raise ValueError(f"unknown action `{action}`")
        moves.append((sid, action, reason))
    before = {s["id"]: (s.get("ref"), s["slot"], s["title"]) for s in r["stories"]}
    for sid, action, reason in moves:
        rank.decide(r, sid, action, reason, by, cfg, now)
    lines = []
    for s in r["stories"]:
        ref, was, title = before[s["id"]]
        if s["slot"] != was:
            lines.append(f"- **{title[:70]}**: {was} → {s['slot']} (was no. {ref}, now no. {s['ref']})")
    approving = any(a == "approve" for _, a, _ in commands)
    if approving:
        rank.approve(r, by, now)
    said = [f"Logged {len(moves)} decision{'s' if len(moves) != 1 else ''}."] if moves else []
    said += lines or (["Nothing changed slot."] if moves else [])
    said.append(f"Approved the {r['week']} ranking. Writing the script from it now; the Review issue follows." if approving
                else "The list at the top of this issue is updated. Comment `approve` when it is right.")
    return ("approve" if approving else "decide"), "\n".join(said)


def main() -> int:
    week = re.search(r"\b(\d{4}-W\d{2})\b", os.environ.get("TITLE", ""))
    by = os.environ.get("ACTOR", "") or "founder"
    try:
        commands = parse_all(os.environ.get("BODY", ""))
        if not week:
            raise ValueError("no week in the issue title")
        r = rank.load(week.group(1))
        if r is None:
            raise ValueError(f"no ranking saved for {week.group(1)}")
        cfg = load_settings()
        kind, result = apply(r, commands, by, cfg)
    except ValueError as e:
        write_outputs(os.environ.get("GITHUB_OUTPUT"), {"kind": "error", "week": "", "result": f"Not applied: {e}"})
        print(f"::warning::{e}")
        return 0
    rank.save(r)
    if os.environ.get("ISSUE_BODY"):
        Path(os.environ["ISSUE_BODY"]).write_text(
            "Updated after your last comment. Move or drop stories with the commands below, then comment `approve`.\n\n"
            + rank.to_md(r, cfg), encoding="utf-8")
    write_outputs(os.environ.get("GITHUB_OUTPUT"), {"kind": kind, "week": r["week"], "result": result})
    return 0


if __name__ == "__main__":
    sys.exit(main())
