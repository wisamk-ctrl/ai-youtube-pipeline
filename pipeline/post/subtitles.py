"""
Phase 4 (optional) — post-production with pip-installable, offline tools.

    talking_head.mp4
        │
        ▼  faster-whisper (local, CPU ok)  → subtitles.srt  (Arabic, word-timed)
        │                                  → transcript check vs. the approved script
        ▼  ffmpeg                          → final_subtitled.mp4 (burned-in RTL captions)
        ▼  ffmpeg                          → shorts/short_01.mp4 … (9:16 cuts for Shorts/Reels)

Why burn captions in here rather than at the avatar provider: HeyGen/D-ID
captions have weak Arabic shaping and no font control; libass (inside ffmpeg)
shapes Arabic correctly via HarfBuzz when given a proper Arabic font.

First run downloads the Whisper model (~1.5 GB for `large-v3`, ~500 MB for
`medium`) from huggingface.co; set WHISPER_MODEL=small for a quick test.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

log = logging.getLogger(__name__)

# Fonts with full Arabic coverage, in preference order. Install Noto with
# `apt install fonts-noto-core` or drop the .ttf into ./fonts.
ARABIC_FONTS = ["Noto Naskh Arabic", "Noto Sans Arabic", "Amiri", "DejaVu Sans"]


@dataclass
class Segment:
    start: float
    end: float
    text: str


def _fmt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


@dataclass
class Word:
    start: float
    end: float
    word: str


def transcribe_words(video: Path, model_size: str | None = None) -> list[Word]:
    """Every word Whisper hears, with its own start and end time."""
    from faster_whisper import WhisperModel  # imported lazily: heavy, optional

    model_size = model_size or os.environ.get("WHISPER_MODEL", "large-v3")
    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, info = model.transcribe(str(video), language="ar", word_timestamps=True, vad_filter=True)
    log.info("Whisper %s: language=%s p=%.2f", model_size, info.language, info.language_probability)
    return [Word(w.start, w.end, w.word) for seg in segments for w in (seg.words or [])]


def transcribe(video: Path, model_size: str | None = None, max_chars: int = 42) -> list[Segment]:
    """Arabic transcription re-chunked into caption-sized lines (Whisper's own wording)."""
    return chunk_words(transcribe_words(video, model_size), max_chars)


def chunk_words(all_words: list[Word], max_chars: int = 42) -> list[Segment]:
    """Whisper's segments can run 15+ seconds; captions over ~42 characters wrap badly on phones,
    so lines are re-split on word timings."""
    out: list[Segment] = []
    words: list = []
    for w in all_words:
        words.append(w)
        line = "".join(x.word for x in words).strip()
        # Flush on length or on a sentence-final mark.
        if len(line) >= max_chars or line.endswith(("،", ".", "؟", "!", "…")):
            out.append(Segment(words[0].start, words[-1].end, line))
            words = []
    if words:
        out.append(Segment(words[0].start, words[-1].end, "".join(x.word for x in words).strip()))
    return out


# ── Captions from the approved script, timed by Whisper ─────────────────────
# Whisper writes Jordanian speech in its own spelling («خلين انبلش» for «خلّينا نبلّش») and
# digits for spoken numbers. The viewer should read the approved script, so Whisper is used only
# for timing: script words are matched to heard words wherever the two agree after normalising
# Arabic spelling, and every other word is timed by interpolating between those anchors.
_HARAKAT = re.compile(r"[\u064B-\u0652\u0670\u0640]")
_PUNCT = re.compile(r"[^\w]", re.UNICODE)


def norm_word(w: str) -> str:
    w = _HARAKAT.sub("", w)
    w = re.sub("[أإآٱ]", "ا", w).replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    return _PUNCT.sub("", w).lower()


def align(script_words: list[str], heard: list[Word]) -> list[float]:
    """A start time for every script word."""
    n = len(script_words)
    if not heard:
        return [0.0] * n
    sm = SequenceMatcher(None, [norm_word(w) for w in script_words], [norm_word(h.word) for h in heard], autojunk=False)
    anchors = {}
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            if norm_word(script_words[a + k]):
                anchors[a + k] = heard[b + k].start
    end = heard[-1].end
    if not anchors:   # nothing matched: spread the script evenly over the speech
        first = heard[0].start
        return [first + (end - first) * i / n for i in range(n)]
    points = sorted(anchors.items())
    if points[0][0] != 0:
        points.insert(0, (0, min(heard[0].start, points[0][1])))
    if points[-1][0] != n:
        points.append((n, end))
    times = []
    for i in range(n):
        for (i0, t0), (i1, t1) in zip(points, points[1:]):
            if i0 <= i <= i1:
                times.append(t0 if i1 == i0 else t0 + (t1 - t0) * (i - i0) / (i1 - i0))
                break
    # Monotonic, whatever the matcher did.
    for i in range(1, n):
        times[i] = max(times[i], times[i - 1])
    log.info("Caption alignment: %d of %d script words anchored to heard words", len(anchors), n)
    return times


def script_captions(spoken_script: str, heard: list[Word], max_chars: int = 42) -> list[Segment]:
    words = spoken_script.split()
    if not words:
        return []
    times = align(words, heard)
    end = heard[-1].end if heard else times[-1] + 2
    lines: list[tuple[int, int]] = []
    start = 0
    for i in range(len(words)):
        text = " ".join(words[start:i + 1])
        if len(text) >= max_chars or words[i].endswith(("،", ".", "؟", "!", "…", ":")) or i == len(words) - 1:
            lines.append((start, i + 1))
            start = i + 1
    out = []
    for k, (a, b) in enumerate(lines):
        t0 = times[a]
        t1 = times[lines[k + 1][0]] if k + 1 < len(lines) else end
        out.append(Segment(t0, max(t0 + 0.4, t1 - 0.05), " ".join(words[a:b])))
    return out


def write_srt(segments: list[Segment], dest: Path) -> Path:
    lines = []
    for i, s in enumerate(segments, 1):
        lines += [str(i), f"{_fmt_ts(s.start)} --> {_fmt_ts(s.end)}", s.text, ""]
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def transcript_matches_script(segments: list[Segment], spoken_script: str) -> float:
    """0..1 similarity between what was said and what was approved.

    Catches a provider that silently dropped a chunk or mangled a number.
    Arabic diacritics/punctuation differ between Whisper and the script, so
    compare on stripped, lower-cased tokens. Expect ~0.85+ for a clean render.
    """
    said = [norm_word(w) for s in segments for w in s.text.split()]
    approved = [norm_word(w) for w in spoken_script.split()]
    return SequenceMatcher(None, " ".join(said), " ".join(approved), autojunk=False).ratio()


def _ffmpeg(*args: str) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found on PATH")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def _font() -> str:
    try:
        installed = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
    except FileNotFoundError:
        installed = ""
    for f in ARABIC_FONTS:
        if f in installed:
            return f
    log.warning("No Arabic font found (%s); captions may render as boxes", ", ".join(ARABIC_FONTS))
    return ARABIC_FONTS[-1]


def burn_in(video: Path, srt: Path, dest: Path, font_size: int = 22) -> Path:
    """Hard-code captions. libass handles RTL shaping; Alignment=2 = bottom-centre."""
    style = f"FontName={_font()},FontSize={font_size},Outline=2,Shadow=0,MarginV=40,Alignment=2"
    # Escape for ffmpeg's filter parser: ':' and '\' inside the path.
    srt_path = str(srt).replace("\\", "\\\\").replace(":", "\\:")
    _ffmpeg("-i", str(video), "-vf", f"subtitles='{srt_path}':force_style='{style}'",
            "-c:a", "copy", str(dest))
    return dest


def cut_short(video: Path, start: float, end: float, dest: Path, srt: Path | None = None) -> Path:
    """A 9:16 vertical cut for Shorts/Reels: centre-crop 16:9 → 9:16, 1080×1920."""
    vf = "crop=ih*9/16:ih,scale=1080:1920"
    if srt:
        srt_path = str(srt).replace("\\", "\\\\").replace(":", "\\:")
        vf += f",subtitles='{srt_path}':force_style='FontName={_font()},FontSize=28,Alignment=2,MarginV=160'"
    _ffmpeg("-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", str(video), "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", str(dest))
    return dest


def run_post(video: Path, spoken_script: str, out_dir: Path, shorts: list[tuple[float, float]] | None = None,
             burn: bool = True) -> dict:
    """Transcribe → SRT → similarity check → burned-in master → optional Shorts."""
    heard = transcribe_words(video)
    segments = chunk_words(heard)
    write_srt(segments, out_dir / "transcript.srt")          # Whisper's own wording, for checking
    srt = write_srt(script_captions(spoken_script, heard), out_dir / "subtitles.srt")
    score = transcript_matches_script(segments, spoken_script)
    log.info("Transcript/script similarity: %.2f", score)
    if score < 0.75:
        log.warning("Low similarity — the render may have dropped or garbled a chunk; review subtitles.srt")

    final = burn_in(video, srt, out_dir / "final_subtitled.mp4") if burn else None
    made = []
    if shorts:
        (out_dir / "shorts").mkdir(exist_ok=True)
    for i, (a, b) in enumerate(shorts or [], 1):
        made.append(cut_short(video, a, b, out_dir / "shorts" / f"short_{i:02d}.mp4", srt))
    return {"srt": srt, "final": final, "similarity": score, "shorts": made}
