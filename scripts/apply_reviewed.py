"""Put reviewed/<week>/script.md in place for a render-side phase.

The hand-edited script wins, except when the week's script.md is that same text with shot
markers added by the director (identical spoken words): then the directed copy is kept, so a
re-run never throws away an approved shot list. Usage: python scripts/apply_reviewed.py <week>
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.script_format import has_shots, spoken_text  # noqa: E402


def main(week: str) -> str:
    reviewed = Path("reviewed") / week / "script.md"
    if not reviewed.exists():
        return "no reviewed script"
    current = Path("output") / week / "script.md"
    current.parent.mkdir(parents=True, exist_ok=True)
    if current.exists():
        cur, rev = current.read_text(encoding="utf-8"), reviewed.read_text(encoding="utf-8")
        if has_shots(cur) and not has_shots(rev) and spoken_text(cur).split() == spoken_text(rev).split():
            return "kept the directed copy of the reviewed script"
    shutil.copy(reviewed, current)
    return "using reviewed script"


if __name__ == "__main__":
    print(main(sys.argv[1]))
