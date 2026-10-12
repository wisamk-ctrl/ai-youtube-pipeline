#!/usr/bin/env python3
"""
Your decisions on radar candidates, applied to the two files that hold them.

    python scripts/radar_decide.py promote "Reflection AI" --track models --group us --ar "ريفلكشن" --alias Beam --hf reflectionai
    python scripts/radar_decide.py ignore "Some Startup"
    python scripts/radar_decide.py list            # candidates by score, with weeks seen

promote  → inserts one line into config/watchlist.yaml under the right track/group (the file's
           comments and layout are left untouched) and marks the name `promoted` in radar_state.json
ignore   → marks the name `ignored` in data/radar_state.json; the radar never surfaces it again

The weekly-roundup workflow runs the same commands from `/promote …` and `/ignore …` comments on
the review issue, so you can decide from your phone.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import ROOT  # noqa: E402
from pipeline.radar.radar import STATE_PATH, load_state, norm, save_state  # noqa: E402

WATCHLIST = ROOT / "config" / "watchlist.yaml"


def _yaml_str(s: str) -> str:
    """Quote a scalar for the flow-style entity line when it contains YAML-significant characters."""
    return f'"{s}"' if re.search(r"[:#,{}\[\]\"']", s) else s


def promote(name: str, track: str, group: str, ar: str = "", aliases: list[str] | None = None,
            hf: str = "", github: str = "", x: str = "", rss: list[str] | None = None,
            watchlist: Path = WATCHLIST, state_path: Path | None = None) -> str:
    text = watchlist.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Locate the group's `entities:` block inside the track: tracks are at 2 spaces,
    # groups at 6, `entities:` at 8, entity lines at 10.
    t_idx = next((i for i, l in enumerate(lines) if l.rstrip() == f"  {track}:"), None)
    if t_idx is None:
        raise SystemExit(f"track {track!r} not found in {watchlist}")
    g_idx = next((i for i in range(t_idx + 1, len(lines)) if lines[i].rstrip() == f"      {group}:"), None)
    next_track = next((i for i in range(t_idx + 1, len(lines)) if re.match(r"^  \w+:\s*$", lines[i])), len(lines))
    if g_idx is None or g_idx > next_track:
        raise SystemExit(f"group {group!r} not found under track {track!r}")
    e_idx = next(i for i in range(g_idx + 1, len(lines)) if lines[i].rstrip() == "        entities:")
    end = e_idx + 1
    while end < len(lines) and lines[end].startswith("          - "):
        end += 1

    if any(norm(name) == norm(m) for m in re.findall(r"\{name: ([^,}]+)", text)):
        return f"{name} is already on the watchlist"

    parts = [f"name: {_yaml_str(name)}"]
    if ar:
        parts.append(f"ar: {_yaml_str(ar)}")
    if aliases:
        parts.append("aliases: [" + ", ".join(_yaml_str(a) for a in aliases) + "]")
    if rss:
        parts.append("rss: [" + ", ".join(rss) + "]")
    if github:
        parts.append(f"github: {github}")
    if hf:
        parts.append(f"hf: {hf}")
    if x:
        parts.append(f"x: {x}")
    lines.insert(end, "          - {" + ", ".join(parts) + "}")
    watchlist.write_text("\n".join(lines), encoding="utf-8")

    _set_status(name, "promoted", state_path)
    return f"promoted {name} → {track}/{group}"


def ignore(name: str, state_path: Path | None = None) -> str:
    _set_status(name, "ignored", state_path)
    return f"ignored {name}"


def _set_status(name: str, status: str, state_path: Path | None) -> None:
    import pipeline.radar.radar as r
    if state_path:
        r.STATE_PATH = state_path
    state = load_state()
    rec = state.setdefault(norm(name), {"name": name, "first_seen": None, "status": "candidate", "weeks": {}})
    rec["status"] = status
    save_state(state)


def list_candidates() -> str:
    state = load_state()
    rows = [(k, v) for k, v in state.items() if v.get("status") == "candidate"]
    rows.sort(key=lambda kv: -max((w.get("score", 0) for w in kv[1].get("weeks", {}).values()), default=0))
    out = [f"{'name':30} {'weeks':>5}  {'best':>5}  track"]
    for k, v in rows[:40]:
        weeks = v.get("weeks", {})
        best = max((w.get("score", 0) for w in weeks.values()), default=0)
        track = next(iter(weeks.values()), {}).get("track", "?")
        out.append(f"{v.get('name', k):30} {len(weeks):>5}  {best:>5}  {track}")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("promote"); p.add_argument("name")
    p.add_argument("--track", required=True, choices=["models", "agents", "chips"])
    p.add_argument("--group", required=True, help="models: us|eu|cn|gulf · agents: frameworks|products|enterprise · chips: makers|hyperscalers|inference")
    p.add_argument("--ar", default=""); p.add_argument("--alias", action="append", default=[])
    p.add_argument("--hf", default=""); p.add_argument("--github", default=""); p.add_argument("--x", default="")
    p.add_argument("--rss", action="append", default=[])
    i = sub.add_parser("ignore"); i.add_argument("name")
    sub.add_parser("list")
    a = ap.parse_args()
    if a.cmd == "promote":
        print(promote(a.name, a.track, a.group, a.ar, a.alias, a.hf, a.github, a.x, a.rss))
    elif a.cmd == "ignore":
        print(ignore(a.name))
    else:
        print(list_candidates())


if __name__ == "__main__":
    main()
