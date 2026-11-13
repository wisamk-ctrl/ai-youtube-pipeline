"""Short-form posting from GitHub Actions (pipeline/publish/social.py).

    python scripts/social.py plan <week>        queue the week's clips; assets go to release social-<week>
    python scripts/social.py post [--id ID]     post every approved, due entry (cron)
    python scripts/social.py approve <week>     approve a week's entries
    python scripts/social.py status             print the queue

The queue is data/social_queue.json (committed by the workflow).
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.config import load_settings  # noqa: E402
from pipeline.language import apply_language  # noqa: E402
from pipeline.publish import social  # noqa: E402

QUEUE = ROOT / "data" / "social_queue.json"


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])}: {r.stderr.strip()[-400:]}")
    return r.stdout


def repo() -> str:
    return os.environ["GITHUB_REPOSITORY"]


def plan(week: str) -> None:
    out = ROOT / "output" / week
    cfg = apply_language(load_settings(), week)
    queue = social.load_queue(QUEUE)
    tag = f"social-{week}"
    base = f"https://github.com/{repo()}/releases/download/{tag}"
    new = social.plan_week(out, cfg, queue, lambda name: f"{base}/{name}")
    if not new:
        print("nothing new to queue")
        return
    files = []
    meta = json.loads((out / "shorts" / "shorts.json").read_text(encoding="utf-8"))
    for n, sh in enumerate(meta, 1):
        src, dst = out / "shorts" / sh["file"], out / "shorts" / f"{week}-short-{n:02d}.mp4"
        dst.write_bytes(src.read_bytes())
        files.append(str(dst))
    try:
        gh("release", "view", tag, "--repo", repo())
    except RuntimeError:
        gh("release", "create", tag, "--repo", repo(), "--title", f"Social clips {week}",
           "--notes", "Vertical clips for Shorts / Reels / TikTok (public URLs Instagram fetches from).", "--prerelease")
    gh("release", "upload", tag, *files, "--repo", repo(), "--clobber")
    social.save_queue(QUEUE, queue)
    for e in new:
        print(f"queued {e['id']} due {e['due']} approved={e['approved']} → {', '.join(e['posts'])}: {e['title']}")


def post(only: str | None) -> int:
    cfg = load_settings()
    queue = social.load_queue(QUEUE)
    work = ROOT / "output" / "social"
    work.mkdir(parents=True, exist_ok=True)

    def fetch(e):
        dest = work / e["file"]
        if not dest.exists():
            tag = f"social-{e['week']}"
            gh("release", "download", tag, "--repo", repo(), "--pattern", e["file"], "--dir", str(work), "--clobber")
        return dest
    lines = social.post_due(queue, cfg, fetch, social.posters(cfg), only=only)
    social.save_queue(QUEUE, queue)
    print("\n".join(lines) or "nothing due")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary and lines:
        Path(summary).write_text("## Social posts\n\n" + "\n".join(f"- {x}" for x in lines) + "\n", encoding="utf-8")
    return 1 if any(x.startswith("❌") for x in lines) else 0


def approve(week: str) -> None:
    queue = social.load_queue(QUEUE)
    n = 0
    for e in queue:
        if e["week"] == week and not e["approved"]:
            e["approved"] = True
            n += 1
    social.save_queue(QUEUE, queue)
    print(f"approved {n} entries of {week}")


def status() -> None:
    for e in social.load_queue(QUEUE):
        posts = ", ".join(f"{p}:{r.get('status')}" for p, r in e["posts"].items())
        print(f"{e['id']}  due {e['due']}  {'approved' if e['approved'] else 'WAITING FOR APPROVAL'}  {posts}  {e['title'][:60]}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["plan", "post", "approve", "status"])
    ap.add_argument("week", nargs="?")
    ap.add_argument("--id")
    a = ap.parse_args()
    if a.action in ("plan", "approve") and not a.week:
        sys.exit("week required")
    if a.action == "plan":
        plan(a.week)
    elif a.action == "post":
        sys.exit(post(a.id))
    elif a.action == "approve":
        approve(a.week)
    else:
        status()
