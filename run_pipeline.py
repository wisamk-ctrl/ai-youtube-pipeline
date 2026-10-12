#!/usr/bin/env python3
"""
Weekly Arabic AI-news roundup — orchestrator.

Every phase reads its input from, and writes its output to, a per-week folder
(output/2026-W41/ ...), so phases can run separately, be re-run after a fix,
or be reviewed by a human in between:

    output/<week>/
      items.json          Phase 1  scored + filtered news items (with score breakdowns)
      plan.json           Phase 2  editorial plan (structured)
      script.md           Phase 2  Arabic script with pacing markers  ← review / edit this
      tts_text.txt        Phase 3  exactly what the voice engine receives
      cue_sheet.json      Phase 3  B-roll / on-screen cues with estimated timestamps
      talking_head.mp4    Phase 3  the rendered digital-twin video
      talking_head.job.txt         provider job ID, for --resume-video-id

Usage:
    python run_pipeline.py ingest
    python run_pipeline.py script
    python run_pipeline.py video [--dry-run]
    python run_pipeline.py all            # stops after the script for human review
    python run_pipeline.py all --approve  # fully unattended (not recommended for a face-and-voice clone)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

from pipeline.config import ROOT, load_settings
from pipeline.models import NewsItem

log = logging.getLogger("pipeline")


def week_dir(week: str | None) -> Path:
    if not week:
        y, w, _ = date.today().isocalendar()
        week = f"{y}-W{w:02d}"
    path = ROOT / "output" / week
    path.mkdir(parents=True, exist_ok=True)
    return path


def phase_ingest(cfg: dict, out: Path) -> None:
    from pipeline.ingestion.engine import run_ingestion

    items = run_ingestion(cfg, week=out.name, out_dir=out)
    (out / "items.json").write_text(
        json.dumps([i.to_dict() for i in items], ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Phase 1 done → %s (%d items)", out / "items.json", len(items))


def phase_script(cfg: dict, out: Path) -> None:
    from pipeline.scripting.script_engine import ScriptEngine

    items_path = out / "items.json"
    if not items_path.exists():
        sys.exit(f"{items_path} not found — run the ingest phase first.")
    items = [NewsItem.from_dict(d) for d in json.loads(items_path.read_text(encoding="utf-8"))]

    result = ScriptEngine(cfg).run(items, week_label=out.name)
    (out / "plan.json").write_text(
        json.dumps(result.plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "script.md").write_text(result.script + "\n", encoding="utf-8")
    (out / "critique.json").write_text(json.dumps(result.critique_rounds, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "source_map.md").write_text(result.source_map_md, encoding="utf-8")
    log.info("Quality: critic %s · sources: %s", 
             " → ".join(str(r["minimum"]) for r in result.critique_rounds) or "n/a", result.source_stats)
    minutes = result.word_count / cfg["scripting"]["words_per_minute"]
    log.info("Phase 2 done → %s (%d words ≈ %.1f min; target %d)",
             out / "script.md", result.word_count, minutes, result.target_words)


def phase_video(cfg: dict, out: Path, dry_run: bool, resume_id: str | None) -> None:
    from pipeline.video.engine import resume_video, run_video

    if resume_id:
        # Accept either the bare ID or the "provider:id" line from talking_head.job.txt.
        resume_video(resume_id.split(":", 1)[-1], cfg, out)
        return

    script_path = out / "script.md"
    if not script_path.exists():
        sys.exit(f"{script_path} not found — run the script phase first.")
    plan_path = out / "plan.json"
    title = json.loads(plan_path.read_text(encoding="utf-8"))["episode_title_ar"] if plan_path.exists() else out.name

    # Reads script.md from disk, so any manual edits made during review are what gets rendered.
    path = run_video(script_path.read_text(encoding="utf-8"), title, cfg, out, dry_run=dry_run)
    if path:
        log.info("Phase 3 done → %s", path)


def phase_post(cfg: dict, out: Path, shorts_arg: str | None) -> None:
    from pipeline.post.subtitles import run_post
    from pipeline.script_format import spoken_text

    video = out / "talking_head.mp4"
    if not video.exists():
        sys.exit(f"{video} not found — run the video phase first.")
    shorts = [tuple(map(float, s.split("-"))) for s in shorts_arg.split(",")] if shorts_arg else []
    result = run_post(video, spoken_text((out / "script.md").read_text(encoding="utf-8")), out, shorts)
    log.info("Phase 4 done → %s (similarity %.2f, %d shorts)", result["final"], result["similarity"], len(result["shorts"]))


def phase_publish(cfg: dict, out: Path) -> None:
    from pipeline.publish.youtube_upload import run_publish

    video_id = run_publish(out, cfg)
    log.info("Phase 5 done → https://youtu.be/%s (private, scheduled)", video_id)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["ingest", "script", "video", "post", "publish", "all"])
    ap.add_argument("--fixture", help="Copy fixtures/<name>/items.json into the week folder instead of ingesting (offline testing)")
    ap.add_argument("--shorts", help='Comma-separated start-end seconds for vertical cuts, e.g. "12-55,180-240"')
    ap.add_argument("--week", help="Output folder name, default: current ISO week (e.g. 2026-W41)")
    ap.add_argument("--config", type=Path, help="Alternate settings.yaml")
    ap.add_argument("--dry-run", action="store_true", help="Prepare TTS text/cues but skip the paid render")
    ap.add_argument("--approve", action="store_true", help="With 'all': render without stopping for script review")
    ap.add_argument("--resume-video-id", help="Re-attach to an already-submitted render job")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    cfg = load_settings(args.config)
    out = week_dir(args.week)

    if args.fixture:
        import shutil
        shutil.copy(ROOT / "fixtures" / args.fixture / "items.json", out / "items.json")
        log.info("Using fixture items from fixtures/%s", args.fixture)
    elif args.phase in ("ingest", "all"):
        phase_ingest(cfg, out)
    if args.phase in ("script", "all"):
        phase_script(cfg, out)
    if args.phase == "all" and not args.approve:
        # Human-in-the-loop gate. The video puts *your* face and voice on these
        # claims; a 5-minute read of script.md is the cheapest insurance there is.
        log.info("Script ready for review: %s\nEdit it if needed, then run: python run_pipeline.py video --week %s",
                 out / "script.md", out.name)
        return
    if args.phase in ("video", "all"):
        phase_video(cfg, out, args.dry_run, args.resume_video_id)
    if args.phase == "post":
        phase_post(cfg, out, args.shorts)
    if args.phase == "publish":
        phase_publish(cfg, out)


if __name__ == "__main__":
    main()
