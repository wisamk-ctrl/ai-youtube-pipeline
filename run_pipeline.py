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

from pipeline import usage
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
    _write_script_result(cfg, out, result, plan_too=True)
    if cfg.get("visuals", {}).get("enabled"):
        script = _directed(cfg, out, result.script)
        from pipeline.video.voicefirst import write_voice_pack
        write_voice_pack(script, cfg, out)          # for the voice-first route (needs the shot markers)
        from pipeline.script_format import count_spoken_words
        _shotlist(cfg, out, script, count_spoken_words(script) / cfg["scripting"]["words_per_minute"] * 60, None)


def _write_script_result(cfg: dict, out: Path, result, plan_too: bool) -> None:
    if plan_too:
        (out / "plan.json").write_text(
            json.dumps(result.plan.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "script.md").write_text(result.script + "\n", encoding="utf-8")
    (out / "critique.json").write_text(json.dumps(result.critique_rounds, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "source_map.md").write_text(result.source_map_md, encoding="utf-8")
    from pipeline.video.manual import write_paste_pack
    write_paste_pack(result.script, cfg, out)   # for the manual HeyGen web-app route
    from pipeline.video.voicefirst import write_voice_pack
    write_voice_pack(result.script, cfg, out)   # voice-first route; skipped until the script is directed
    log.info("Quality: critic %s · sources: %s",
             " → ".join(str(r["minimum"]) for r in result.critique_rounds) or "n/a", result.source_stats)
    minutes = result.word_count / cfg["scripting"]["words_per_minute"]
    log.info("Script → %s (%d words ≈ %.1f min; target %d)",
             out / "script.md", result.word_count, minutes, result.target_words)


def _load_week(out: Path):
    from pipeline.scripting.script_engine import EditorialPlan
    for name in ("items.json", "plan.json", "script.md", "critique.json"):
        if not (out / name).exists():
            sys.exit(f"{out / name} not found — run the script phase first.")
    items = [NewsItem.from_dict(d) for d in json.loads((out / "items.json").read_text(encoding="utf-8"))]
    plan = EditorialPlan.model_validate(json.loads((out / "plan.json").read_text(encoding="utf-8")))
    script = (out / "script.md").read_text(encoding="utf-8").rstrip("\n")
    rounds = json.loads((out / "critique.json").read_text(encoding="utf-8"))
    return items, plan, script, rounds


def _items(out: Path) -> list[NewsItem]:
    p = out / "items.json"
    return [NewsItem.from_dict(d) for d in json.loads(p.read_text(encoding="utf-8"))] if p.exists() else []


def _directed(cfg: dict, out: Path, script: str) -> str:
    """The script with shot markers: as written if it has them, otherwise through the director pass."""
    from pipeline.script_format import has_shots
    if has_shots(script):
        return script
    from pipeline.scripting.director import direct
    directed = direct(script, _items(out), cfg)
    (out / "script.md").write_text(directed.rstrip("\n") + "\n", encoding="utf-8")
    return directed


def _shotlist(cfg: dict, out: Path, script: str, duration: float, srt: Path | None,
              hides: list | None = None, face_only: list | None = None) -> list:
    from pipeline.post import visuals
    v = cfg.get("visuals", {})
    shots = visuals.plan(script, duration, srt, cfg["scripting"]["words_per_minute"],
                         max_visual=float(v.get("max_visual_seconds", 12)),
                         card_max=float(v.get("max_card_seconds", 5)),
                         corner=bool(v.get("corner", {}).get("enabled", False)),
                         face_mode=str(v.get("face_mode", "normal")),
                         face_keep=float(v.get("face_keep_seconds", 8)), hide=hides,
                         face_only=face_only)
    report = visuals.lint(shots, v)
    titles = {i.id: f"{i.source}: {i.title[:90]}" for i in _items(out)}
    (out / "shotlist.md").write_text(visuals.shotlist_md(shots, report, estimated=srt is None, titles=titles), encoding="utf-8")
    (out / "shotlist.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Shot list: face %.0f%%, %d shots, %d warnings", report["face_share"] * 100, report["shots"], len(report["warnings"]))
    return shots


def phase_score(cfg: dict, out: Path) -> None:
    """Score the script as it stands (critic + source map), without rewriting it.

    Reads reviewed/<week>/script.md when present, so a hand-edited script is what gets scored."""
    from pipeline.scripting.script_engine import ScriptEngine

    items, plan, script, rounds = _load_week(out)
    reviewed = ROOT / "reviewed" / out.name / "script.md"
    if reviewed.exists():
        script = reviewed.read_text(encoding="utf-8").rstrip("\n")
        log.info("Scoring the reviewed script %s", reviewed)
    result = ScriptEngine(cfg).score(plan, script, items, rounds, week=out.name)
    _write_script_result(cfg, out, result, plan_too=False)


def phase_polish(cfg: dict, out: Path) -> None:
    """Apply the last critique's fixes to the existing script and score it again (no regeneration)."""
    from pipeline.scripting.script_engine import ScriptEngine

    items, plan, script, rounds = _load_week(out)
    (out / f"script.before-polish-{len(rounds)}.md").write_text(script + "\n", encoding="utf-8")
    result = ScriptEngine(cfg).polish(plan, script, items, rounds, week=out.name)
    _write_script_result(cfg, out, result, plan_too=False)


def _sources_gate(out: Path, phase: str, warn_only: bool = False) -> None:
    """No render or import while the week's source map shows unsourced claims (review Tier 1 #8)."""
    from pipeline.scripting.source_map import gate
    ok, msg = gate(out)
    if ok:
        (log.warning if "not audited" in msg else log.info)("Sources: %s", msg)
        return
    if warn_only:
        log.warning("Sources (dry run, not blocking): %s", msg)
        return
    sys.exit(f"phase {phase}: {msg}")


def phase_video(cfg: dict, out: Path, dry_run: bool, resume_id: str | None) -> None:
    from pipeline.video.engine import resume_video, run_video

    if resume_id:
        # Accept either the bare ID or the "provider:id" line from talking_head.job.txt.
        # A render already paid for is collected; the gate applies to new renders.
        resume_video(resume_id.split(":", 1)[-1], cfg, out)
        return
    _sources_gate(out, "video", warn_only=dry_run)

    script_path = out / "script.md"
    if not script_path.exists():
        sys.exit(f"{script_path} not found — run the script phase first.")
    plan_path = out / "plan.json"
    title = json.loads(plan_path.read_text(encoding="utf-8"))["episode_title_ar"] if plan_path.exists() else out.name

    # Reads script.md from disk, so any manual edits made during review are what gets rendered.
    path = run_video(script_path.read_text(encoding="utf-8"), title, cfg, out, dry_run=dry_run)
    if path:
        log.info("Phase 3 done → %s", path)


def _repair_speech(cfg: dict, out: Path, video: Path, spoken: str):
    """Re-voice the phrases the render got wrong (post/repair.py). Returns (video, face-hide spans,
    heard words or None). The original talking_head.mp4 is left untouched so the edit can re-run."""
    if not cfg.get("post", {}).get("repair", {}).get("enabled", True):
        return video, [], None
    from pipeline.post import repair
    from pipeline.post.subtitles import transcribe_words
    plan = repair.load_voice(ROOT / "reviewed" / out.name)
    if plan is None:
        return video, [], None
    src = out / "talking_head.source.txt"
    if src.exists() and src.read_text(encoding="utf-8").startswith("voice-first"):
        log.info("Voice-first or own-voice recording: no speech repair (repairs.yaml is for avatar renders)")
        for stale in ("repairs.md", "repairs.json"):   # an earlier avatar run's report must not be posted again
            (out / stale).unlink(missing_ok=True)
        return video, [], None
    if plan["render"] and src.exists() and plan["render"] not in src.read_text(encoding="utf-8"):
        log.warning("repairs.yaml is for render %s, not this one; no speech repair", plan["render"])
        return video, [], None
    heard = transcribe_words(video)
    repairs, skipped = repair.find(spoken, heard, cfg, plan["fix"])
    for r in repairs:
        # Nothing left to say (a dropped gloss): cut it to a short pause, no clip needed.
        r.audio = plan["voice"].get(repair.key(r.say), "") or ("" if repair.key(r.say) else "silence:0.15")
    (out / "repairs.json").write_text(json.dumps([vars(r) for r in repairs], ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    fps = int(cfg.get("visuals", {}).get("fps", 30))
    video, hides, heard = repair.apply(video, repairs, heard, out, fps)
    (out / "repairs.md").write_text(repair.report_md(repairs, skipped), encoding="utf-8")
    log.info("Speech repair: %d found, %d re-voiced, %d left", len(repairs), sum(1 for r in repairs if r.audio), len(skipped))
    return video, hides, heard


def _dur(path: Path) -> float:
    from pipeline.post.edit import duration
    return duration(path)


def _check_length(stage: str, path: Path, expected: float, tolerance: float = 1.5) -> None:
    """Every stage must keep the programme's length. W45 (2026-11-07) came out 6:21 instead of ~9:20
    with no error anywhere; a short stage now stops the run and says which one."""
    got = _dur(path)
    log.info("Length check — %s: %.1f s (expected %.1f s)", stage, got, expected)
    if got < expected - tolerance:
        sys.exit(f"{stage} is {got:.1f} s, expected {expected:.1f} s: the edit lost {expected - got:.1f} s "
                 f"({path.name}). Not publishing a truncated episode.")


def phase_post(cfg: dict, out: Path, shorts_arg: str | None) -> None:
    from pipeline.post.subtitles import run_post
    from pipeline.script_format import spoken_text

    video = out / "talking_head.mp4"
    if not video.exists():
        sys.exit(f"{video} not found — run the video phase first.")
    shorts = [tuple(map(float, s.split("-"))) for s in shorts_arg.split(",")] if shorts_arg else []
    script = (out / "script.md").read_text(encoding="utf-8")
    from pipeline.post import repair
    plan = repair.load_voice(ROOT / "reviewed" / out.name)
    if plan and plan["correct"]:
        script = repair.apply_corrections(script, plan["correct"])
        (out / "script.md").write_text(script, encoding="utf-8")
    from pipeline.post.subtitles import burn_in
    video, hides, heard = _repair_speech(cfg, out, video, spoken_text(script))
    result = run_post(video, spoken_text(script), out, [], burn=False, heard=heard)   # Shorts: post/shorts.py below
    base, skip = video, []
    if cfg.get("visuals", {}).get("enabled"):
        # The premium cut (config/visual_standard.md): face for ~a quarter, visuals for the rest.
        from pipeline.post import edit, visual_assets
        script = _directed(cfg, out, script)
        from pipeline.video.voicefirst import face_spans
        shots = _shotlist(cfg, out, script, edit.duration(video), result["srt"], hides, face_spans(out))
        clips, _ = visual_assets.build(shots, _items(out), cfg, out)
        from pipeline.post.audio import section_times
        base = edit.compose(video, shots, clips, cfg, out,
                            sections=section_times(script, result["srt"], cfg["scripting"]["words_per_minute"]))
        skip = [(s.start, s.end) for n, s in enumerate(shots) if n in clips and s.kind in ("number", "title", "source")]
        _check_length("edited cut", base, edit.duration(video))
    if cfg.get("post", {}).get("overlays", {}).get("enabled", True):
        from pipeline.post.overlays import run_overlays
        base = run_overlays(base, script, cfg, out, result["srt"], skip_spans=skip)
        _check_length("with cue cards", base, _dur(video))
    # Final audio (music bed, whooshes, loudness) and the sting, then the one high-quality encode.
    from pipeline.post import audio
    sting = audio.sting_plan(cfg, script, result["srt"], base, ROOT)
    mix = audio.master(base, out / "final_audio.wav", cfg, out / "audio",
                       insert=sting, cuts=audio.section_times(script, result["srt"], cfg["scripting"]["words_per_minute"]))
    from pipeline.post import packaging, shorts as shorts_mod
    tail = packaging.end_card(cfg, out)          # 15 s branded end card (post.end_card), no captions over it
    result["final"] = burn_in(base, result["srt"], out / "final_subtitled.mp4", audio=mix, insert=sting, tail=tail)
    extra = (audio.duration_of(sting[1]) if sting else 0) + (audio.duration_of(tail) if tail else 0)
    _check_length("final (programme + sting + end card)", result["final"], _dur(video) + extra)
    sting_span = (sting[0], audio.duration_of(sting[1])) if sting else None
    if sting:   # the captions as they sit in the final cut (for a caption-track upload)
        audio.shift_srt(result["srt"], sting[0], sting_span[1], out / "subtitles.final.srt")
    # The YouTube package: chapters' timeline, thumbnail, native vertical Shorts (from the edit, pre-sting).
    packaging.write_timeline(out, script, result["srt"], cfg, sting_span,
                             audio.duration_of(tail) if tail else None, audio.duration_of(result["final"]))
    try:
        packaging.render_thumbnail(out, cfg, talking_head=out / "talking_head.mp4")
    except Exception as e:  # noqa: BLE001 — a thumbnail must not sink the episode
        log.warning("Thumbnail failed: %s", e)
    try:
        result["shorts"] = shorts_mod.build(base, script, result["srt"], shorts, cfg, out, sting=sting_span)
    except Exception as e:  # noqa: BLE001
        log.warning("Shorts failed: %s", e)
    import shutil  # intermediates are as large as the video itself; keep the artifact lean
    (out / "talking_head.repaired.mp4").unlink(missing_ok=True)
    if mix:
        mix.unlink(missing_ok=True)
    for tmp in ("segments", "visuals", "repair", "audio", "endcard"):
        shutil.rmtree(out / tmp, ignore_errors=True)
    log.info("Phase 4 done → %s (similarity %.2f, %d shorts)", result["final"], result["similarity"], len(result["shorts"]))


def phase_import(cfg: dict, out: Path, video_ref: str | None) -> None:
    """Manual route: bring in a video rendered in HeyGen's web app, then run post-production."""
    from pipeline.video.manual import import_video

    if not video_ref:
        sys.exit("phase import needs --video-url (a HeyGen video ID or link, Drive, Dropbox or direct MP4 URL)")
    if not (out / "script.md").exists():
        sys.exit(f"{out / 'script.md'} not found — the week needs its script for subtitles and cue cards.")
    _sources_gate(out, "import")
    import_video(video_ref, out)
    phase_post(cfg, out, None)


def phase_direct(cfg: dict, out: Path) -> None:
    """Run the director on the week's approved script and write the shot list, before any video exists."""
    from pipeline.script_format import count_spoken_words
    if not (out / "script.md").exists():
        sys.exit(f"{out / 'script.md'} not found — run the script phase first.")
    from pipeline.script_format import strip_shots
    # Always a fresh plan: an earlier one (perhaps the rule-based fallback) is discarded.
    script = _directed(cfg, out, strip_shots((out / "script.md").read_text(encoding="utf-8")))
    from pipeline.video.voicefirst import write_voice_pack
    write_voice_pack(script, cfg, out)
    _shotlist(cfg, out, script, count_spoken_words(script) / cfg["scripting"]["words_per_minute"] * 60, None)


def phase_voicepack(cfg: dict, out: Path) -> None:
    """Voice-first route, step 1: the speech chunks of the directed script (voice_pack.md)."""
    from pipeline.video.voicefirst import write_voice_pack
    if not (out / "script.md").exists():
        sys.exit(f"{out / 'script.md'} not found — run the script phase first.")
    write_voice_pack(_directed(cfg, out, (out / "script.md").read_text(encoding="utf-8")), cfg, out)


def phase_assemble(cfg: dict, out: Path, check_only: bool = False) -> None:
    """Voice-first route, step 3: speech chunks + face videos (reviewed/<week>/voice.yaml) →
    talking_head.mp4, then post-production."""
    from pipeline.video import voicefirst
    if not (out / "voice_pack.json").exists():
        phase_voicepack(cfg, out)
    _sources_gate(out, "assemble")
    voice = ROOT / "reviewed" / out.name / "voice.yaml"
    if not voice.exists():
        sys.exit(f"{voice} not found — make the speech and face videos from voice_pack.md first.")
    chunks = json.loads((out / "voice_pack.json").read_text(encoding="utf-8"))["chunks"]
    try:
        entries = voicefirst.load_voice(voice, chunks)
    except ValueError as exc:
        sys.exit(f"phase assemble: {exc}")
    from pipeline.script_format import spoken_text
    spoken = spoken_text((out / "script.md").read_text(encoding="utf-8"))
    read = ROOT / "reviewed" / out.name / "read_script.md"
    if read.exists():   # the own-voice edit follows what the founder read from (names as said, no glosses)
        from pipeline.video.guided import reading_text
        spoken = reading_text(read.read_text(encoding="utf-8")) or spoken
    if check_only:
        try:
            voicefirst.voice_check(entries, cfg, out, spoken)
        except ValueError as exc:
            sys.exit(f"phase voicecheck: {exc}")
        return
    voicefirst.assemble(entries, cfg, out, spoken)
    phase_post(cfg, out, None)


def phase_translate(cfg: dict, out: Path) -> None:
    """English version: output/<week> (directed Arabic script) → output/<week>-en (same sources and
    shot plan; English words, voice, captions, on-screen text). --week may name either folder."""
    import copy
    from pipeline.language import apply_language, english_week, source_week
    from pipeline.scripting import translate
    src, dst = ROOT / "output" / source_week(out.name), ROOT / "output" / english_week(out.name)
    try:
        summary = translate.run(src, dst, cfg)
    except (FileNotFoundError, translate.TranslationError) as exc:
        sys.exit(f"phase translate: {exc}")
    cfg_en = apply_language(copy.deepcopy(cfg), dst.name)
    script = (dst / "script.md").read_text(encoding="utf-8")
    from pipeline.video.manual import write_paste_pack
    write_paste_pack(script, cfg_en, dst)              # manual route, with the English voice clone
    if cfg.get("visuals", {}).get("enabled"):
        from pipeline.script_format import count_spoken_words
        _shotlist(cfg_en, dst, script, count_spoken_words(script) / cfg["scripting"]["words_per_minute"] * 60, None)
    log.info("English version → %s: %s", dst, summary)


def phase_publish(cfg: dict, out: Path) -> None:
    from pipeline.publish.youtube_upload import run_publish

    video_id = run_publish(out, cfg)
    log.info("Phase 5 done → https://youtu.be/%s (private, scheduled)", video_id)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phase", choices=["ingest", "script", "polish", "score", "direct", "video", "import", "post", "publish",
                                     "voicepack", "voicecheck", "assemble", "translate", "all"])
    ap.add_argument("--fixture", help="Copy fixtures/<name>/items.json into the week folder instead of ingesting (offline testing)")
    ap.add_argument("--shorts", help='Comma-separated start-end seconds for vertical cuts, e.g. "12-55,180-240"')
    ap.add_argument("--week", help="Output folder name, default: current ISO week (e.g. 2026-W41)")
    ap.add_argument("--config", type=Path, help="Alternate settings.yaml")
    ap.add_argument("--dry-run", action="store_true", help="Prepare TTS text/cues but skip the paid render")
    ap.add_argument("--approve", action="store_true", help="With 'all': render without stopping for script review")
    ap.add_argument("--resume-video-id", help="Re-attach to an already-submitted render job")
    ap.add_argument("--video-url", help="import: HeyGen video ID or link, Drive/Dropbox share link, or direct MP4 URL")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    cfg = load_settings(args.config)
    out = week_dir(args.week)
    from pipeline.language import apply_language
    apply_language(cfg, out.name)                      # an <week>-en folder is the English version
    if cfg["language"] == "en" and args.phase in ("ingest", "script", "polish", "score", "all"):
        sys.exit(f"phase {args.phase} is the Arabic writer/critic; for {out.name} re-run phase translate on its Arabic week")
    _RUN["out"] = out                                 # for the top-level error handler
    (out / ERROR_FILE).unlink(missing_ok=True)         # a stale error must not outlive its run

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
        usage.write(out, cfg.get("pricing"))
        return
    if args.phase in ("video", "all"):
        phase_video(cfg, out, args.dry_run, args.resume_video_id)
    if args.phase == "polish":
        phase_polish(cfg, out)
    if args.phase == "score":
        phase_score(cfg, out)
    if args.phase == "direct":
        phase_direct(cfg, out)
    if args.phase == "voicepack":
        phase_voicepack(cfg, out)
    if args.phase == "voicecheck":   # own-voice route: the cleaned read alone, before any video
        phase_assemble(cfg, out, check_only=True)
    if args.phase == "assemble":
        phase_assemble(cfg, out)
    if args.phase == "import":
        phase_import(cfg, out, args.video_url)
    if args.phase == "post":
        phase_post(cfg, out, args.shorts)
    if args.phase == "translate":
        phase_translate(cfg, out)
    if args.phase == "publish":
        phase_publish(cfg, out)
    usage.write(out, cfg.get("pricing"))


ERROR_FILE = "error.txt"   # read by .github/workflows/weekly.yml for the run-failed issue
_RUN: dict = {}


def write_error(out: Path | None, exc: BaseException) -> Path | None:
    """Put the failure (a sys.exit message or the traceback) in output/<week>/error.txt."""
    if out is None:
        return None
    import traceback
    if isinstance(exc, SystemExit):
        text = f"{exc.code}\n"
    else:
        text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        path = out / ERROR_FILE
        path.write_text(text[-20000:], encoding="utf-8")
        return path
    except OSError:
        return None


def _entry() -> None:
    try:
        main()
    except SystemExit as e:
        if e.code not in (None, 0):
            write_error(_RUN.get("out"), e)
        raise
    except BaseException as e:   # noqa: BLE001 — record, then fail as before
        write_error(_RUN.get("out"), e)
        raise


if __name__ == "__main__":
    _entry()
