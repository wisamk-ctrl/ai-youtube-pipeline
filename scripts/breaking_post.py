"""The founder's OK for a breaking Short: approve its social queue entry, due now, with its LinkedIn post.

Usage: python scripts/breaking_post.py <week>   (after `social.py plan <week>`)"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))   # `python scripts/breaking_post.py` must find the pipeline package


def approve(week: str, queue: Path = ROOT / "data" / "social_queue.json", root: Path = ROOT, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    meta = yaml.safe_load((root / "reviewed" / week / "breaking.yaml").read_text(encoding="utf-8")) or {}
    s = yaml.safe_load((root / "config" / "settings.yaml").read_text(encoding="utf-8")).get("social", {})
    tags = " ".join(s.get("linkedin_hashtags_en", []))
    note = "Presented by my AI digital twin, with my consent. Informational only."
    q, n = json.loads(queue.read_text(encoding="utf-8")), 0
    for e in q:
        if e["week"] != week:
            continue
        e["approved"], e["due"] = True, now.strftime("%Y-%m-%dT%H:%M:%SZ")
        tt = e["captions"].get("tiktok", "")
        e["captions"]["tiktok"] = tt.replace("Full episode on YouTube: link in bio",
                                             "More on this in Sunday's episode of AI This Week. Follow so you don't miss it.")
        if meta.get("linkedin") and "linkedin" in e["captions"]:
            from pipeline.publish.social import follow_line
            follow = follow_line(s)
            e["captions"]["linkedin"] = (f"{meta['linkedin'].strip()}\n\nMore on this in Sunday's episode of AI This Week."
                                         f"{follow}\n\n{note}\n\n{tags}").strip()
        n += 1
    queue.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")
    return n


if __name__ == "__main__":
    print(f"approved {approve(sys.argv[1])} entr(ies) for {sys.argv[1]}")
