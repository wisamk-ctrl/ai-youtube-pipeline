"""Quality check of a finished Short before the founder sees it (founder 2026-11-19).

    python scripts/short_check.py <short.mp4> [<short.srt>]   → a Markdown report; exit 0 always

Checks: length (≤ 180 s), loudness (−16 to −12 LUFS) and true peak (≤ −1 dBTP), dead air (> 1.2 s of
silence before the end card), a frozen picture (> 11 s, the card limit), and captions: a word alone on
screen ("Face", 2026-11-18) and a caption held longer than 7 s."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

END_CARD = 5.0     # the closing card and outro: silence and stillness there are by design


def _ffmpeg(path: Path, af: str = "", vf: str = "") -> str:
    args = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path)]
    args += ["-af", af] if af else ["-an"]
    args += ["-vf", vf] if vf else ["-vn"]
    return subprocess.run(args + ["-f", "null", "-"], capture_output=True, text=True).stderr


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


def _ts(t: str) -> float:
    h, m, s = t.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def caption_faults(srt_text: str) -> list[str]:
    bad = []
    for block in re.split(r"\n\s*\n", srt_text.strip()):
        lines = block.strip().splitlines()
        m = next((re.match(r"(\S+) --> (\S+)", ln) for ln in lines if "-->" in ln), None)
        if not m:
            continue
        text = " ".join(ln for ln in lines[lines.index(m.string) + 1:]).strip()
        a, b = _ts(m.group(1)), _ts(m.group(2))
        words = text.split()
        if len(words) == 1 and not text.endswith(("?", "!", "؟")):
            bad.append(f"a word alone on screen at {a:.1f} s: “{text}”")
        if b - a > 7.0:
            bad.append(f"a caption held {b - a:.1f} s at {a:.1f} s: “{text[:40]}”")
    return bad


def check(video: Path, srt: Path | None = None) -> tuple[list[str], list[str]]:
    """(faults, facts)."""
    faults, facts = [], []
    d = duration(video)
    facts.append(f"length {d:.1f} s")
    if d > 180:
        faults.append(f"longer than 3 minutes ({d:.0f} s): YouTube will not treat it as a Short")
    loud = _ffmpeg(video, af="ebur128=peak=true")
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)
    pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", loud)
    if i:
        lufs = float(i[-1])
        facts.append(f"loudness {lufs:.1f} LUFS")
        if not -16.0 <= lufs <= -12.0:
            faults.append(f"loudness {lufs:.1f} LUFS (aim −14)")
    if pk:
        peak = float(pk[-1])
        facts.append(f"peak {peak:.1f} dB")
        if peak > -1.0:
            faults.append(f"true peak {peak:.1f} dB (could clip on phones)")
    for st, en in re.findall(r"silence_start: (-?[\d.]+)[\s\S]*?silence_end: ([\d.]+)",
                             _ffmpeg(video, af="silencedetect=n=-40dB:d=1.2")):
        if float(st) < d - END_CARD:
            faults.append(f"dead air {float(en) - float(st):.1f} s at {float(st):.1f} s")
    for st, dur in re.findall(r"freeze_start: ([\d.]+)[\s\S]*?freeze_duration: ([\d.]+)",
                              _ffmpeg(video, vf="freezedetect=n=0.003:d=11")):
        if float(st) < d - END_CARD:
            faults.append(f"picture frozen {float(dur):.1f} s at {float(st):.1f} s")
    if srt and srt.exists():
        faults += caption_faults(srt.read_text(encoding="utf-8"))
    return faults, facts


def report(video: Path, srt: Path | None = None) -> str:
    faults, facts = check(video, srt)
    head = "✅ **Automatic check passed**" if not faults else f"⚠️ **Automatic check: {len(faults)} to look at**"
    return "\n".join([f"{head} ({', '.join(facts)})", *[f"- {f}" for f in faults]])


if __name__ == "__main__":
    v = Path(sys.argv[1])
    print(report(v, Path(sys.argv[2]) if len(sys.argv) > 2 else v.with_suffix(".srt")))
