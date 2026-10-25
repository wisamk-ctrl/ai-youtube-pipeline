"""
Manual render route: the presenter renders in HeyGen's web app (on the monthly subscription,
not API credits) and the pipeline carries on from the finished video.

1. paste_pack(): the approved script as paste-ready scenes for HeyGen's editor. Production
   markers are removed, [Pause] becomes "...", and the text is split at sentence boundaries
   into scenes small enough for one script box each.
2. import_video(): fetch the rendered video into the week folder as talking_head.mp4, from a
   HeyGen video ID or share link, a Google Drive or Dropbox share link, or a direct MP4 URL.
   The file is checked with ffprobe before it is accepted.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import requests

from pipeline.script_format import chunk_text, count_spoken_words, to_tts_text
from pipeline.video.common import download

log = logging.getLogger(__name__)

HEX_ID = re.compile(r"\b([0-9a-f]{32})\b")


def paste_scenes(script: str, cfg: dict[str, Any]) -> list[str]:
    text = to_tts_text(script, "ellipsis", cfg["video"]["pause_seconds"])
    return chunk_text(text, cfg["video"]["max_chars_per_chunk"])


def paste_pack(script: str, cfg: dict[str, Any], week: str) -> str:
    scenes = paste_scenes(script, cfg)
    minutes = count_spoken_words(script) / cfg["scripting"]["words_per_minute"]
    h = cfg["video"]["heygen"]
    lines = [
        f"# HeyGen paste pack · {week}",
        "",
        f"{len(scenes)} scenes · about {minutes:.1f} minutes.",
        "",
        "1. In HeyGen, create a video with your avatar and your voice clone"
        + (f" (avatar `{h.get('avatar_id')}`, voice `{h.get('voice_id')}`)." if h.get("avatar_id") else "."),
        "2. Make one scene per block below and paste each block into its scene's script box, in order.",
        "   The \"...\" marks are pauses; keep them.",
        f"3. Render at {h.get('width', 1920)}×{h.get('height', 1080)} if your plan allows, otherwise 1080p.",
        "4. Copy the video's ID or share link and run weekly-roundup with phase `import`, this week,",
        "   and that link in `video_url`. Cue cards and subtitles are added automatically.",
        "",
    ]
    for n, s in enumerate(scenes, 1):
        lines += [f"## Scene {n}", "", "```", s.strip(), "```", ""]
    return "\n".join(lines)


def write_paste_pack(script: str, cfg: dict[str, Any], out_dir: Path) -> Path:
    p = out_dir / "heygen_paste.md"
    p.write_text(paste_pack(script, cfg, out_dir.name), encoding="utf-8")
    return p


def resolve(ref: str, api_key: str | None = None) -> str:
    """Turn what the presenter pastes into a direct download URL."""
    ref = ref.strip()
    if not ref:
        raise ValueError("video_url is empty")
    if "heygen" in ref or HEX_ID.fullmatch(ref):
        m = HEX_ID.search(ref)
        if not m:
            raise ValueError(f"No HeyGen video ID in {ref!r}")
        return heygen_url(m.group(1), api_key or os.environ.get("HEYGEN_API_KEY", ""))
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:.*&)?id=)([\w-]{20,})", ref)
    if m:
        return f"https://drive.usercontent.google.com/download?id={m.group(1)}&export=download&confirm=t"
    if "dropbox.com" in ref:
        return re.sub(r"([?&])dl=0", r"\1dl=1", ref) if "dl=0" in ref else ref + ("&" if "?" in ref else "?") + "dl=1"
    if ref.startswith(("http://", "https://")):
        return ref
    raise ValueError(f"Not a URL or HeyGen video ID: {ref!r}")


def heygen_url(video_id: str, api_key: str) -> str:
    """A status lookup, not a render: it reads the download link of a video already made in the app."""
    if not api_key:
        raise RuntimeError("HEYGEN_API_KEY is needed to look up a HeyGen video by ID")
    r = requests.get("https://api.heygen.com/v1/video_status.get", params={"video_id": video_id},
                     headers={"X-Api-Key": api_key, "Accept": "application/json"}, timeout=60)
    r.raise_for_status()
    data = r.json().get("data") or {}
    if data.get("status") != "completed" or not data.get("video_url"):
        raise RuntimeError(f"HeyGen video {video_id} is not ready: status={data.get('status')} error={data.get('error')}")
    return data["video_url"]


def probe(path: Path) -> dict[str, Any]:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                          "-of", "json", str(path)], capture_output=True, text=True)
    if out.returncode != 0:
        raise ValueError(f"{path.name} is not a readable video: {out.stderr.strip()[:200]}")
    info = json.loads(out.stdout)
    video = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    audio = [s for s in info.get("streams", []) if s.get("codec_type") == "audio"]
    duration = float(info.get("format", {}).get("duration") or 0)
    if not video or not audio or duration < 10:
        raise ValueError(f"{path.name} is not a talking-head video (video={bool(video)}, audio={bool(audio)}, {duration:.0f}s)")
    return {"duration": duration, "width": video[0].get("width"), "height": video[0].get("height")}


def import_video(ref: str, out_dir: Path) -> Path:
    url = resolve(ref)
    dest = out_dir / "talking_head.mp4"
    download(url, dest)
    try:
        info = probe(dest)
    except ValueError:
        dest.unlink(missing_ok=True)
        raise
    (out_dir / "talking_head.source.txt").write_text(f"manual import\nfrom: {ref.strip()}\n{json.dumps(info)}\n", encoding="utf-8")
    log.info("Imported %s: %.0f s, %sx%s", dest, info["duration"], info["width"], info["height"])
    return dest
