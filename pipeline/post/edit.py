"""
The editor: cut the episode from the presenter's video and the visual clips, over the
presenter's own audio track (config/visual_standard.md).

Each shot becomes a segment of exactly its frame count, all with the same size, rate and codec,
so the segments concatenate without re-encoding and the picture never drifts from the voice.
Every cut is hard except at a [Section] boundary, where a short dissolve joins the two (one extra
encode of the whole cut, only when there is a dissolve).
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


def dissolve_shots(shots: list[Shot], sections: list[float] | None, near: float = 1.5) -> set[int]:
    """Shots that open a [Section]: the shot boundary nearest each section time, within `near` s."""
    out: set[int] = set()
    starts = [(n, s.start) for n, s in enumerate(shots) if n > 0]
    for t in sections or []:
        if starts:
            n, at = min(starts, key=lambda x: abs(x[1] - t))
            if abs(at - t) <= near:
                out.add(n)
    return out


def compose(talking_head: Path, shots: list[Shot], clips: dict[int, Path], cfg: dict[str, Any], out_dir: Path,
            sections: list[float] | None = None) -> Path:
    """The cut. Hard cuts everywhere except where a [Section] starts (`sections`, seconds): there a
    short dissolve (visuals.dissolve_frames, 12). The outgoing segment runs on by the dissolve's
    length, so the picture keeps its frame count and never drifts from the untouched audio."""
    v = cfg.get("visuals", {})
    w, h, fps = int(v.get("width", 1920)), int(v.get("height", 1080)), int(v.get("fps", 30))
    fade = int(v.get("dissolve_frames", 12))
    seg_dir = out_dir / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    fill = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps}"
    spans = [(n, round(s.start * fps), round(s.end * fps)) for n, s in enumerate(shots)]
    spans = [x for x in spans if x[2] > x[1]]
    want = dissolve_shots(shots, sections) if fade > 0 else set()
    # A dissolve needs room on both sides; index into `spans` of each segment that dissolves in.
    dissolve = {k for k in range(1, len(spans)) if spans[k][0] in want
                and min(spans[k][2] - spans[k][1], spans[k - 1][2] - spans[k - 1][1]) > fade}
    runs: list[list[str]] = [[]]
    for k, (n, f0, f1) in enumerate(spans):
        s = shots[n]
        frames = f1 - f0 + (fade if k + 1 in dissolve else 0)
        start = f0 / fps
        seg = seg_dir / f"seg_{n:03d}.mp4"
        clip = clips.get(n)
        mode = s.mode if (s.mode == "face" or clip) else "face"
        if mode == "face":
            _ff("-ss", f"{start:.3f}", "-i", str(talking_head), "-vf", fill, "-frames:v", str(frames), *_enc(fps), str(seg))
        elif mode == "visual":
            _ff("-i", str(clip), "-vf", f"scale={w}:{h},fps={fps},tpad=stop_mode=clone:stop_duration=2",
                "-frames:v", str(frames), *_enc(fps), str(seg))
        else:
            graph, *_ = corner_filter(w, h, cfg)
            _ff("-i", str(clip), "-ss", f"{start:.3f}", "-i", str(talking_head), "-filter_complex", graph,
                "-map", "[out]", "-frames:v", str(frames), *_enc(fps), str(seg))
        got = round(duration(seg) * fps)
        if got < frames - 1:   # a short segment shortens the whole cut (W45, 2026-11-07); say which one
            log.warning("Segment %d (%s %s) is %d frames, expected %d", n, mode, s.kind, got, frames)
        if k in dissolve:
            runs.append([])
        runs[-1].append(f"file '{seg.resolve()}'")
    dest = out_dir / "edited.mp4"
    audio = ["-map", f"{len(runs) if len(runs) > 1 else 1}:a", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(dest)]
    if len(runs) == 1:
        (seg_dir / "list.txt").write_text("\n".join(runs[0]) + "\n", encoding="utf-8")
        _ff("-f", "concat", "-safe", "0", "-i", str(seg_dir / "list.txt"), "-i", str(talking_head),
            "-map", "0:v", "-c:v", "copy", *audio)
    else:
        # Each run between dissolves is stream-copied together; one encode joins the runs with xfade.
        inputs: list[str] = []
        for r, listing in enumerate(runs):
            (seg_dir / f"list_{r}.txt").write_text("\n".join(listing) + "\n", encoding="utf-8")
            _ff("-f", "concat", "-safe", "0", "-i", str(seg_dir / f"list_{r}.txt"), "-c", "copy", str(seg_dir / f"run_{r}.mp4"))
            inputs += ["-i", str(seg_dir / f"run_{r}.mp4")]
        f_first = spans[0][1]
        graph, prev = [], "[0:v]"
        for r, k in enumerate(sorted(dissolve), start=1):
            at = (spans[k][1] - f_first) / fps      # the cut's own time: the outgoing run holds on through it
            graph.append(f"{prev}[{r}:v]xfade=transition=fade:duration={fade / fps:.4f}:offset={at:.4f}[x{r}]")
            prev = f"[x{r}]"
        total = spans[-1][2] - f_first
        _ff(*inputs, "-i", str(talking_head), "-filter_complex", ";".join(graph), "-map", prev,
            "-frames:v", str(total), *[x for x in _enc(fps) if x != "-an"], *audio)
    log.info("Edited cut → %s (%d segments, %d dissolves)", dest, len(spans), len(dissolve))
    return dest
