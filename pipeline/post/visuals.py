"""
Shot timeline: where each shot starts and ends in the rendered video, and whether the episode
meets the visual standard (config/visual_standard.md).

Timing: Whisper's subtitle segments give real times. A script word offset maps to a time by
scaling it onto the transcript's words (the two counts differ a little), then snaps to the
nearest subtitle start within a couple of seconds, so cuts land on sentence starts.
Without subtitles (the review issue, before any video exists) times come from words per minute.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.script_format import count_spoken_words, extract_shots


@dataclass
class Shot:
    mode: str            # face | visual | corner
    kind: str            # "" | source | number | title | stock
    payload: str
    start: float
    end: float
    notes: list[str] = field(default_factory=list)

    @property
    def seconds(self) -> float:
        return self.end - self.start


def read_srt(srt: Path | None) -> list[tuple[float, float, str]]:
    if not srt or not srt.exists():
        return []
    ts = r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d)"
    out = []
    for block in re.split(r"\n\s*\n", srt.read_text(encoding="utf-8").strip()):
        m = re.search(ts + r"\s*-->\s*" + ts, block)
        if not m:
            continue
        g = list(map(int, m.groups()))
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        text = " ".join(l for l in block.splitlines()[2:] if l.strip())
        out.append((a, b, text))
    return out


def word_clock(segments: list[tuple[float, float, str]]) -> list[float]:
    """The start time of every transcript word, spreading each segment's words across its span."""
    times: list[float] = []
    for a, b, text in segments:
        words = text.split() or [""]
        step = (b - a) / len(words)
        times += [a + k * step for k in range(len(words))]
    return times


def plan(script: str, duration: float, srt: Path | None = None, wpm: int = 130,
         snap: float = 2.0, min_shot: float = 1.5, max_visual: float = 12.0,
         corner: bool = True, face_mode: str = "normal", face_keep: float = 8.0,
         hide: list[tuple[float, float]] | None = None) -> list[Shot]:
    """Shot timeline for the edit.

    `corner=False` (visuals.corner.enabled off) renders every corner shot as a full-screen visual.
    `face_mode="minimal"` keeps the presenter's face only for the opening and the sign-off (each at
    most `face_keep` seconds); every other face shot becomes a house tech animation.
    `hide` spans (repaired speech, see post/repair.py) never show the face: the voice there no
    longer matches the lips."""
    marks = extract_shots(script)
    total_words = max(1, count_spoken_words(script))
    segs = read_srt(srt)
    clock = word_clock(segs)
    starts = [a for a, _, _ in segs]

    def at(word: int) -> float:
        if clock:
            t = clock[min(len(clock) - 1, round(word * len(clock) / total_words))]
            near = min(starts, key=lambda s: abs(s - t))
            return near if abs(near - t) <= snap else t
        return word / wpm * 60 * (duration / max(1e-6, total_words / wpm * 60))

    shots: list[Shot] = []
    if not marks:
        return [Shot("face", "", "", 0.0, duration)]
    if marks[0].at_word > 0:
        shots.append(Shot("face", "", "", 0.0, 0.0))
    for mk in marks:
        t = 0.0 if mk.at_word == 0 else at(mk.at_word)
        mode = "visual" if mk.mode == "corner" and not corner else mk.mode
        shots.append(Shot(mode, mk.kind, mk.payload, t, t))
    # Close each shot at the next one's start; drop zero-length shots, then merge slivers forward.
    shots.sort(key=lambda s: s.start)
    for a, b in zip(shots, shots[1:]):
        a.end = b.start
    shots[-1].end = duration
    shots = [s for s in shots if s.end - s.start > 1e-3]
    merged: list[Shot] = []
    for s in shots:
        if merged and s.mode == "face" and merged[-1].mode == "face":
            merged[-1].end = s.end      # two [Face] markers in a row are one continuous shot
            continue
        if merged and s.seconds < min_shot:
            merged[-1].end = s.end
            merged[-1].notes.append(f"absorbed a {s.seconds:.1f}s {s.mode} shot")
            continue
        merged.append(s)
    if merged:
        merged[0].start = 0.0
        merged[-1].end = duration
    # A full-screen visual that runs long switches to the corner layout halfway: same picture,
    # the presenter's circle joins, so the shot changes without inventing a new visual.
    out: list[Shot] = []
    for s in merged:
        if s.mode == "visual" and s.seconds > max_visual:
            mid = s.start + s.seconds / 2
            out.append(Shot("visual", s.kind, s.payload, s.start, mid, s.notes + ["split: long visual"]))
            if corner:
                out.append(Shot("corner", s.kind, s.payload, mid, s.end, ["split: second half in corner layout"]))
            else:
                out.append(Shot("visual", s.kind, s.payload, mid, s.end, ["split: second half of a long visual"]))
        else:
            out.append(s)
    return _less_face(out, face_mode, face_keep, hide or [])


# The house look for shots that were face: a wider rotation than the director's eight, so a
# minimal-face episode does not loop the same few clips.
HOUSE_EXTRA = ["futuristic user interface hologram animation", "glowing fiber optic cables, macro",
               "binary code rain, blue", "robot arm in a modern lab", "data visualization dashboard, dark theme",
               "quantum computer close-up, golden light", "network cables plugged into a switch",
               "programmer typing at night, screen glow", "satellite orbiting earth at night",
               "smart city night lights, timelapse", "microchip production line", "abstract AI brain made of light",
               "cloud computing icons, animation", "cybersecurity padlock hologram", "motherboard close-up, slow pan",
               "server room corridor, slow walk"]


def _less_face(shots: list[Shot], face_mode: str, keep: float, hide: list[tuple[float, float]]) -> list[Shot]:
    from pipeline.scripting.director import HOUSE_STOCK
    pool = HOUSE_STOCK + HOUSE_EXTRA
    house = iter(range(10_000))

    def visual(a: float, b: float, why: str) -> Shot:
        return Shot("visual", "stock", pool[next(house) % len(pool)], a, b, [why])

    def split_hidden(s: Shot) -> list[Shot]:
        """Face shot minus the repaired spans: the face stays where its lips still match the voice."""
        cuts = sorted((max(s.start, a - 0.2), min(s.end, b + 0.2)) for a, b in hide if a < s.end and b > s.start)
        if not cuts:
            return [s]
        pieces, t = [], s.start
        for a, b in cuts:
            if a > t:
                pieces.append(("face", t, a))
            pieces.append(("hide", max(a, t), b))
            t = max(t, b)
        if t < s.end:
            pieces.append(("face", t, s.end))
        out: list[Shot] = []
        for kind, a, b in pieces:      # face slivers under a second read as a glitch: cover them too
            kind = "hide" if kind == "face" and b - a < 1.0 else kind
            if out and kind == "hide" and out[-1].mode == "visual":
                out[-1].end = b
            elif kind == "hide":
                out.append(visual(a, b, "face hidden: repaired speech") if s.mode == "face"
                           else Shot("visual", s.kind, s.payload, a, b, ["corner hidden: repaired speech"]))
            else:
                out.append(Shot(s.mode, s.kind, s.payload, a, b, s.notes))
        return out

    faces = [n for n, s in enumerate(shots) if s.mode == "face"]
    trimmed: list[Shot] = []
    for n, s in enumerate(shots):
        if s.mode != "face" or face_mode != "minimal":
            trimmed.append(s)
        elif n == faces[0] and s.seconds > keep:
            trimmed += [Shot("face", "", "", s.start, s.start + keep, s.notes), visual(s.start + keep, s.end, "minimal face")]
        elif n == faces[-1] and n != faces[0] and s.seconds > keep:
            trimmed += [visual(s.start, s.end - keep, "minimal face"), Shot("face", "", "", s.end - keep, s.end, s.notes)]
        elif n in (faces[0], faces[-1]):
            trimmed.append(s)
        else:
            trimmed.append(visual(s.start, s.end, "minimal face"))
    out: list[Shot] = []
    for s in trimmed:
        out += split_hidden(s) if s.mode in ("face", "corner") and hide else [s]
    return out


def lint(shots: list[Shot], std: dict[str, Any] | None = None) -> dict[str, Any]:
    std = std or {}
    lo, hi = std.get("face_share", [0.10, 0.20])
    cap = std.get("face_share_max", 0.25)
    max_face, max_visual = std.get("max_face_seconds", 12), std.get("max_visual_seconds", 12)
    total = sum(s.seconds for s in shots) or 1.0
    face = sum(s.seconds for s in shots if s.mode == "face")
    share = face / total
    warnings = []
    if std.get("face_mode") == "minimal":
        lo = 0.0       # founder choice 2026-11-07: face only at the open and the sign-off
    if share > cap or share < lo:
        warnings.append(f"face on screen {share:.0%} (standard: {lo:.0%}–{hi:.0%}, never above {cap:.0%})")
    for s in shots:
        if s.mode == "face" and s.seconds > max_face:
            warnings.append(f"{s.seconds:.0f}s face stretch at {s.start:.0f}s (max {max_face}s)")
        if s.mode != "face" and s.seconds > max_visual:
            warnings.append(f"{s.seconds:.0f}s {s.kind} shot at {s.start:.0f}s (max {max_visual}s; the clip will loop or hold)")
    kinds = {k: sum(1 for s in shots if s.kind == k) for k in ("source", "number", "title", "stock")}
    return {"face_share": round(share, 3), "shots": len(shots), "kinds": kinds,
            "corner": sum(1 for s in shots if s.mode == "corner"), "warnings": warnings}


def shotlist_md(shots: list[Shot], report: dict[str, Any], estimated: bool, titles: dict[str, str] | None = None) -> str:
    def ts(x: float) -> str:
        return f"{int(x // 60)}:{int(x % 60):02d}"
    head = [f"## Shot list{' (estimated timings)' if estimated else ''}", "",
            f"Face on screen **{report['face_share']:.0%}** · {report['shots']} shots · "
            + " · ".join(f"{v} {k}" for k, v in report["kinds"].items()) + f" · {report['corner']} corner", ""]
    if report["warnings"]:
        head += ["⚠️ Against the visual standard:"] + [f"- {w}" for w in report["warnings"]] + [""]
    else:
        head += ["✅ Meets the visual standard.", ""]
    rows = ["| time | shot | content |", "|---|---|---|"]
    for s in shots:
        label = {"face": "face", "visual": f"{s.kind}", "corner": f"{s.kind} + corner"}[s.mode]
        content = (titles or {}).get(s.payload, s.payload) if s.kind == "source" else s.payload
        rows.append(f"| {ts(s.start)}–{ts(s.end)} | {label} | {content.replace('|', '/') if content else ''} |")
    return "\n".join(head + ["<details><summary>All shots</summary>", ""] + rows + ["", "</details>"]) + "\n"
