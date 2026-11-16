"""The second check on every figure shown on screen (founder rule 2026-11-15: vetted twice).

The first check is the source trace the founder signs off. This one is mechanical: every figure in a
`[Visual: number …]` card or an `[On-Screen Text: …]` cue must be spoken in the script, and must appear
in the week's source map. A figure that fails either stops the edit.

    python scripts/number_check.py reviewed/<week>/script.md <source_map.md>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CUE = re.compile(r"^\[(Visual: number|On-Screen Text):?\s*(.+?)\]\s*$", re.M)
MARK = re.compile(r"^\[[^\]]*\]\s*$", re.M)
NUM = re.compile(r"\d+(?:[.,]\d+)*")
WORDS = {"trillion": "t", "billion": "b", "million": "m"}


def figures(text: str) -> list[str]:
    """The numbers in a cue as plain digits: '$1.5 trillion' → ['1.5'], '40 of 41' → ['40', '41']."""
    return [n.replace(",", "") for n in NUM.findall(text)]


def check(script: str, sources: str) -> list[str]:
    spoken = set(figures(MARK.sub(" ", script)))
    cited = set(figures(sources))
    problems = []
    for m in CUE.finditer(script):
        kind, body = m.group(1), m.group(2)
        shown = body.split("|")[0] if kind.startswith("Visual") else body
        if re.search(r"\bv?\d+\.\d+\.\d+\b", shown):          # a software version, not a figure
            continue
        for n in figures(shown):
            if n not in spoken:
                problems.append(f"{shown.strip()!r}: {n} is on screen but never spoken")
            elif n not in cited:
                problems.append(f"{shown.strip()!r}: {n} is not in the text of this week's sources")
    return problems


def source_text(items_json: Path) -> str:
    import json
    items = json.loads(items_json.read_text(encoding="utf-8")) if items_json.exists() else []
    return "\n".join(f"{i.get('title', '')}\n{i.get('summary', '')}" for i in items)


if __name__ == "__main__":
    src = Path(sys.argv[2])
    bad = check(Path(sys.argv[1]).read_text(encoding="utf-8"),
                source_text(src) if src.suffix == ".json" else src.read_text(encoding="utf-8"))
    print("\n".join(bad) if bad else "Every on-screen figure is spoken and in the source map.")
    sys.exit(1 if bad else 0)
