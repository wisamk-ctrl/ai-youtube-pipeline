"""
The editor: cut the episode from the presenter's video and the visual clips, over the
presenter's own audio track (config/visual_standard.md).

Each shot becomes a segment of exactly its frame count, all with the same size, rate and codec,
so the segments concatenate without re-encoding and the picture never drifts from the voice.
- face   → that span of the presenter's video, scaled to fill
- visual → the visual clip
- corner → the visual clip with the presenter in a gold-ringed circle, bottom-left, clear of the
           subtitles (bottom-centre) and the cue cards (bottom-right)
The presenter's audio runs untouched under the whole cut.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from pipeline.post.visuals import Shot

log = logging.getLogger(__name__)


def _ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def duration(video: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)],
                         capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def _enc(fps: int) -> list[str]:
    return ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps),
            "-video_track_timescale", str(fps * 1000)]


def corner_filter(w: int, h: int, cfg: dict[str, Any]) -> tuple[str, int, int, int]:
    """filter_complex body for [0]=visual, [1]=presenter → [out]; also returns the circle geometry."""
    c = cfg.get("visuals", {}).get("corner", {})
    size = int(round(h * float(c.get("size", 0.26)) / 2) * 2)
    ring = max(4, int(h * 0.006))
    x = int(w * float(c.get("margin_x", 0.04)))
    y = int(h - size - h * float(c.get("margin_bottom", 0.2)))
    face_crop = float(c.get("face_crop", 0.62))      # share of the frame height kept around the face
    face_top = float(c.get("face_top", 0.06))        # where the crop starts, from the top
    r, R = size / 2, size / 2 + ring
    graph = (
        f"[1:v]crop=ih*{face_crop}:ih*{face_crop}:(iw-ih*{face_crop})/2:ih*{face_top},scale={size}:{size},"
        f"format=yuva444p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(lte(hypot(X-{r},Y-{r}),{r}),255,0)'[pip];"
        f"color=c=0xE8B24A:s={size + 2 * ring}x{size + 2 * ring},format=yuva444p,"
        f"geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(lte(hypot(X-{R},Y-{R}),{R}),255,0)'[ring];"
        f"[0:v][ring]overlay={x - ring}:{y - ring}:shortest=1[b];[b][pip]overlay={x}:{y}:shortest=1,format=yuv420p[out]"
    )
    return graph, size, x, y


def compose(talking_head: Path, shots: list[Shot], clips: dict[int, Path], cfg: dict[str, Any], out_dir: Path) -> Path:
    v = cfg.get("visuals", {})
    w, h, fps = int(v.get("width", 1920)), int(v.get("height", 1080)), int(v.get("fps", 30))
    seg_dir = out_dir / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    fill = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps}"
    listing = []
    for n, s in enumerate(shots):
        f0, f1 = round(s.start * fps), round(s.end * fps)
        frames = f1 - f0
        if frames <= 0:
            continue
        start = f0 / fps
        seg = seg_dir / f"seg_{n:03d}.mp4"
        clip = clips.get(n)
        mode = s.mode if (s.mode == "face" or clip) else "face"
        if mode == "face":
            _ff("-ss", f"{start:.3f}", "-i", str(talking_head), "-vf", fill, "-frames:v", str(frames), *_enc(fps), str(seg))
        elif mode == "visual":
            _ff("-i", str(clip), "-vf", f"scale={w}:{h},fps={fps}", "-frames:v", str(frames), *_enc(fps), str(seg))
        else:
            graph, *_ = corner_filter(w, h, cfg)
            _ff("-i", str(clip), "-ss", f"{start:.3f}", "-i", str(talking_head), "-filter_complex", graph,
                "-map", "[out]", "-frames:v", str(frames), *_enc(fps), str(seg))
        listing.append(f"file '{seg.resolve()}'")
    (seg_dir / "list.txt").write_text("\n".join(listing) + "\n", encoding="utf-8")
    dest = out_dir / "edited.mp4"
    _ff("-f", "concat", "-safe", "0", "-i", str(seg_dir / "list.txt"), "-i", str(talking_head),
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(dest))
    log.info("Edited cut → %s (%d segments)", dest, len(listing))
    return dest
