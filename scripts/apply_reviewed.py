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
    for name in ("items.json", "plan.json"):   # a breaking-news Short has no script run: its sources come from here
        src = reviewed.parent / name
        if src.exists() and not (current.parent / name).exists():
            shutil.copy(src, current.parent / name)
    rev_items, cur_items = reviewed.parent / "items.json", current.parent / "items.json"
    if rev_items.exists() and cur_items.exists():   # a story added by hand brings its source (W47 California, 2026-11-20)
        import json
        have = json.loads(cur_items.read_text(encoding="utf-8"))
        urls = {i.get("url") for i in have}   # saved items carry no "id": it is computed from the url
        extra = [i for i in json.loads(rev_items.read_text(encoding="utf-8")) if i.get("url") not in urls]
        if extra:
            cur_items.write_text(json.dumps(have + extra, ensure_ascii=False, indent=1), encoding="utf-8")
    return "using reviewed script"


def apply_meta(week: str, out_dir: Path | None = None) -> str:
    """reviewed/<week>/meta.yaml (title, description, thumbnail text) wins over the generated plan.json:
    the plan is written before a story is added by hand (W46-en: the title left out the lead story)."""
    import json
    import yaml
    meta, plan = Path("reviewed") / week / "meta.yaml", (out_dir or Path("output") / week) / "plan.json"
    if not meta.exists() or not plan.exists():
        return "no reviewed title or description"
    data = json.loads(plan.read_text(encoding="utf-8"))
    over = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
    data.update({k: v for k, v in over.items() if isinstance(v, (str, list))})
    plan.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return "using reviewed " + ", ".join(sorted(over))


if __name__ == "__main__":
    print(main(sys.argv[1]))
    print(apply_meta(sys.argv[1]))
