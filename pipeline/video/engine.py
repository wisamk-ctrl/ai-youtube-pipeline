"""Phase 3 entry point: approved script → TTS text + cue sheet → avatar MP4."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from pipeline.script_format import chunk_text, extract_cues, to_tts_text

log = logging.getLogger(__name__)


def _provider(cfg: dict[str, Any]):
    """Import lazily so the unused provider's env vars are never required."""
    name = cfg["video"]["provider"]
    if name == "heygen":
        from pipeline.video.heygen_client import HeyGenClient
        return HeyGenClient(cfg)
    if name == "elevenlabs_did":
        from pipeline.video.elevenlabs_did_client import ElevenLabsDIDPipeline
        return ElevenLabsDIDPipeline(cfg)
    raise ValueError(f"Unknown video provider {name!r} (expected heygen | elevenlabs_did)")


def prepare(script: str, cfg: dict[str, Any], out_dir: Path) -> list[str]:
    """Write the speech text and the editor's B-roll cue sheet; return the TTS chunks."""
    v = cfg["video"]
    tts = to_tts_text(script, v["pause_style"], v["pause_seconds"])
    chunks = chunk_text(tts, v["max_chars_per_chunk"])
    (out_dir / "tts_text.txt").write_text("\n\n---\n\n".join(chunks), encoding="utf-8")

    cues = extract_cues(script, cfg["scripting"]["words_per_minute"])
    (out_dir / "cue_sheet.json").write_text(
        json.dumps([asdict(c) for c in cues], ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Prepared %d TTS chunks and %d production cues", len(chunks), len(cues))
    return chunks


def run_video(script: str, title: str, cfg: dict[str, Any], out_dir: Path, dry_run: bool = False) -> Path | None:
    chunks = prepare(script, cfg, out_dir)
    if dry_run:
        log.info("Dry run: skipping the paid render. Inspect %s/tts_text.txt", out_dir)
        return None
    return _provider(cfg).render(chunks, title, out_dir / "talking_head.mp4")


def resume_video(job_id: str, cfg: dict[str, Any], out_dir: Path) -> Path:
    """Re-attach to an already-submitted render (IDs are saved in talking_head.job.txt)."""
    return _provider(cfg).resume(job_id, out_dir / "talking_head.mp4")
