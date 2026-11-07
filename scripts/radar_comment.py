#!/usr/bin/env python3
"""
Turn a `/promote …` or `/ignore …` issue comment into a scripts/radar_decide.py call.

Used by .github/workflows/radar-decide.yml. The comment arrives in the BODY environment variable and
never passes through a shell: the flags are split with shlex and handed to radar_decide.py as an
argument list. The results (kind, name, branch, result) are written to $GITHUB_OUTPUT with a random
heredoc delimiter, so a multi-line result or a hostile name cannot add outputs of its own.

    /promote Reflection AI --track models --group us --ar ريفلكشن --alias Beam --hf reflectionai
    /ignore Some Startup
"""

from __future__ import annotations

import os
import re
import secrets
import shlex
import subprocess
import sys
from pathlib import Path

DECIDE = Path(__file__).resolve().parent / "radar_decide.py"


def parse(body: str) -> tuple[str, str, list[str]]:
    """(kind, name, flags) from the comment's first line. Raises ValueError on anything else."""
    line = (body or "").strip().splitlines()[0].strip() if (body or "").strip() else ""
    if line.startswith("/promote "):
        rest = line[len("/promote "):]
        # The name is everything up to the first ` --flag` (names have spaces and no quotes).
        name, _, flags = rest.partition(" --")
        try:
            argv = shlex.split("--" + flags) if flags else []
        except ValueError as e:
            raise ValueError(f"could not read the flags: {e}") from None
        bad = [a for a in argv if a.startswith("--") and a.split("=", 1)[0] not in
               ("--track", "--group", "--ar", "--alias", "--hf", "--github", "--x", "--rss")]
        if bad:
            raise ValueError(f"unknown flag(s): {' '.join(bad)}")
        kind = "promote"
    elif line.startswith("/ignore "):
        name, argv, kind = line[len("/ignore "):], [], "ignore"
    else:
        raise ValueError("the comment must start with /promote or /ignore")
    name = name.strip()
    if not name or name.startswith("-"):
        raise ValueError("no candidate name")
    return kind, name, argv


def branch_for(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "candidate"
    return f"watchlist/{slug[:60]}"


def write_outputs(path: str | None, values: dict[str, str]) -> None:
    lines = []
    for k, v in values.items():
        delim = f"EOF_{secrets.token_hex(12)}"
        lines += [f"{k}<<{delim}", v, delim]
    text = "\n".join(lines) + "\n"
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


def main() -> int:
    try:
        kind, name, flags = parse(os.environ.get("BODY", ""))
    except ValueError as e:
        print(f"::error::{e}")
        return 1
    run = subprocess.run([sys.executable, str(DECIDE), kind, name, *flags], capture_output=True, text=True)
    sys.stdout.write(run.stdout)
    sys.stderr.write(run.stderr)
    if run.returncode != 0:
        return run.returncode
    write_outputs(os.environ.get("GITHUB_OUTPUT"), {
        "kind": kind, "name": name, "branch": branch_for(name), "result": run.stdout.strip()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
