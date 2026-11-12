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

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from pipeline.script_format import caption_text, spoken_words, unbraced

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


HEARD_CACHE = "heard.json"   # in the week folder, next to talking_head.mp4; travels in the artifact
_HEARD_KEEP = 12             # entries kept (talking_head, a repaired cut, own-voice files and pickups …)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _cache_read(cache: Path, key: str) -> list[Word] | None:
    try:
        entries = json.loads(cache.read_text(encoding="utf-8")).get("entries", {})
        hit = entries.get(key)
        return None if hit is None else [Word(float(s), float(e), str(w)) for s, e, w in hit["words"]]
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None   # missing or damaged cache: transcribe again


def _cache_write(cache: Path, key: str, words: list[Word]) -> None:
    try:
        entries = json.loads(cache.read_text(encoding="utf-8")).get("entries", {}) if cache.exists() else {}
        if not isinstance(entries, dict):
            entries = {}
    except (OSError, ValueError, AttributeError):
        entries = {}
    entries.pop(key, None)
    entries[key] = {"words": [[w.start, w.end, w.word] for w in words]}
    entries = dict(list(entries.items())[-_HEARD_KEEP:])
    try:
        cache.write_text(json.dumps({"version": 1, "entries": entries}, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        log.warning("Could not write the transcript cache %s: %s", cache, e)


def heard_key(video: Path, model_size: str | None = None, language: str | None = None) -> str:
    """The transcript-cache key `transcribe_words` uses for this file."""
    from pipeline.language import week_language
    model_size = model_size or os.environ.get("WHISPER_MODEL", "large-v3")
    return f"{_sha256(Path(video))}:{model_size}:{language or week_language(Path(video).resolve().parent.name)}"


def remember(video: Path, words: list[Word]) -> None:
    """Store words already known for this file (the own-voice edit knows them), so post skips Whisper."""
    _cache_write(Path(video).parent / HEARD_CACHE, heard_key(video), words)


def transcribe_words(video: Path, model_size: str | None = None, cache: Path | None | bool = True,
                     language: str | None = None, vad: bool = True, key: str | None = None) -> list[Word]:
    """Every word Whisper hears, with its own start and end time.

    Cached in <video folder>/heard.json, keyed by the video file's sha256, the model and the language, so a
    post re-run on the same talking_head (repair and run_post both land here) skips Whisper.
    `cache=False` disables it; a Path puts it elsewhere."""
    model_size = model_size or os.environ.get("WHISPER_MODEL", "large-v3")
    # The week folder names the language: output/<week>-en is the English version (pipeline/language.py).
    from pipeline.language import week_language
    language = language or week_language(Path(video).resolve().parent.name)
    cache_path = (Path(video).parent / HEARD_CACHE) if cache is True else (cache or None)
    key = (key or f"{_sha256(Path(video))}:{model_size}:{language}" + ("" if vad else ":novad")) if cache_path else ""
    if cache_path:
        hit = _cache_read(cache_path, key)
        if hit is not None:
            log.info("Whisper %s: %d words from %s (same video, same model)", model_size, len(hit), cache_path.name)
            return hit

    from faster_whisper import WhisperModel  # imported lazily: heavy, optional

    model = WhisperModel(model_size, device="auto", compute_type="int8")
    segments, info = model.transcribe(str(video), language=language, word_timestamps=True, vad_filter=vad)
    log.info("Whisper %s: language=%s p=%.2f", model_size, info.language, info.language_probability)
    words = [Word(w.start, w.end, w.word) for seg in segments for w in (seg.words or [])]
    if cache_path:
        _cache_write(cache_path, key, words)
    return words


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


def anchor_map(script_words: list[str], heard: list[Word], min_block: int = 1) -> dict[int, int]:
    """Script word index → index of the heard word it was matched to (only where the two agree).

    `min_block=2` keeps only matches inside runs of two or more agreeing words, so a lone «و» or
    «في» matched by chance is not trusted as a splice point."""
    sm = SequenceMatcher(None, [norm_word(w) for w in script_words], [norm_word(h.word) for h in heard], autojunk=False)
    out = {}
    for a, b, size in sm.get_matching_blocks():
        if size < min_block:
            continue
        for k in range(size):
            if norm_word(script_words[a + k]):
                out[a + k] = b + k
    return out


def align(script_words: list[str], heard: list[Word]) -> list[float]:
    """A start time for every script word."""
    n = len(script_words)
    if not heard:
        return [0.0] * n
    anchors = {i: heard[j].start for i, j in anchor_map(script_words, heard).items()}
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
    """Braced names («أوبن إيه آي{OpenAI}») are timed on the Arabic the voice said and shown
    as «أوبن إيه آي (OpenAI)»."""
    tokens = spoken_words(spoken_script)
    if not tokens:
        return []
    times = align([unbraced(t) for t in tokens], heard)
    words = [caption_text(t).strip() for t in tokens]
    end = heard[-1].end if heard else times[-1] + 2
    lines: list[tuple[int, int]] = []
    start = 0
    for i in range(len(words)):
        text = " ".join(words[start:i + 1])
        if len(text) >= max_chars or words[i].endswith((".", "؟", "?", "!", "…")) or i == len(words) - 1:
            lines.append((start, i + 1))
            start = i + 1
    out = []
    for k, (a, b) in enumerate(lines):
        t0 = times[a]
        t1 = times[lines[k + 1][0]] if k + 1 < len(lines) else end
        # Subtitle convention: no trailing comma, full stop or colon (they also flip sides next to
        # Latin words in right-to-left text); questions and exclamations keep their mark.
        text = " ".join(words[a:b]).strip().rstrip("،,.:؛;").strip()
        out.append(Segment(t0, max(t0 + 0.4, t1 - 0.05), text))
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


_LATIN_RUN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.%+\-]*(?:[ .\-][A-Za-z0-9][A-Za-z0-9.%+\-]*)*")


def isolate_latin(text: str) -> str:
    """Wrap each Latin run (names, versions, figures) in FSI…PDI, so the bidi algorithm lays it out
    as one left-to-right unit inside the Arabic line instead of flipping its punctuation and words."""
    return _LATIN_RUN.sub(lambda m: f"⁨{m[0]}⁩", text)


def _isolated_srt(srt: Path, dest: Path) -> Path:
    lines = srt.read_text(encoding="utf-8").splitlines()
    out = [ln if (not ln.strip() or ln.strip().isdigit() or "-->" in ln) else isolate_latin(ln) for ln in lines]
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    return dest


def _geometry(video: Path) -> tuple[str, int, int]:
    """(frame rate as ffprobe writes it, width, height) of the first video stream."""
    import json
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate,width,height",
                        "-of", "json", str(video)], capture_output=True, text=True, check=True)
    st = json.loads(r.stdout)["streams"][0]
    return st.get("r_frame_rate", "30/1"), int(st["width"]), int(st["height"])


def burn_in(video: Path, srt: Path, dest: Path, font_size: int = 54, audio: Path | None = None,
            insert: tuple[float, Path] | None = None, tail: Path | None = None) -> Path:
    """Hard-code captions in the episode's one final, high-quality encode. libass handles RTL shaping.

    Captions sit in a translucent navy box (BorderStyle=3), ~54 px on a 1080p frame (PlayRes is set
    to the frame, so sizes are pixels). `audio` replaces the soundtrack (post/audio.master);
    `insert=(t, sting.mp4)` splices the sting's picture in at t, after the captions are drawn, so
    every caption after it moves with the picture."""
    fps, w, h = _geometry(video)
    scale = h / 1080
    style = (f"PlayResX={w},PlayResY={h},FontName={_font()},FontSize={round(font_size * scale)},PrimaryColour=&H00F4F1EA,"
             f"BorderStyle=3,Outline={max(1, round(10 * scale))},OutlineColour=&H50201209,BackColour=&H50201209,"
             f"Shadow=0,MarginV={round(56 * scale)},MarginL={round(120 * scale)},MarginR={round(120 * scale)},Alignment=2")
    iso = _isolated_srt(srt, dest.with_suffix(".isolated.srt"))
    # Escape for ffmpeg's filter parser: ':' and '\' inside the path.
    srt_path = str(iso).replace("\\", "\\\\").replace(":", "\\:")
    subs = f"subtitles='{srt_path}':original_size={w}x{h}:force_style='{style}'"
    args = ["-i", str(video)]
    if insert:
        at, sting = insert
        args += ["-i", str(sting)]
        graph = (f"[0:v]{subs},split=2[s1][s2];[s1]trim=end={at:.3f},setpts=PTS-STARTPTS[v1];"
                 f"[s2]trim=start={at:.3f},setpts=PTS-STARTPTS[v2];"
                 f"[1:v]scale={w}:{h},fps={fps},format=yuv420p,setsar=1[st];[v1][st][v2]concat=n=3:v=1:a=0[v]")
        vmap = ["-filter_complex", graph, "-map", "[v]"]
    else:
        vmap = ["-vf", subs, "-map", "0:v"]
    if audio:
        args += ["-i", str(audio)]
        amap = ["-map", f"{len(args) // 2 - 1}:a"]
    else:
        amap = ["-map", "0:a?"]
    if tail:   # the end card (post/packaging.py): its own picture and sound after the programme, no captions
        graph = vmap[1] if insert else f"[0:v]{subs}[v]"
        a_in = amap[1].rstrip("?")
        args += ["-i", str(tail)]
        k = len(args) // 2 - 1
        graph += (f";[v]format=yuv420p,setsar=1[pv];[{k}:v]scale={w}:{h},fps={fps},format=yuv420p,setsar=1[tv];"
                  f"[{a_in}]aformat=sample_rates=48000:channel_layouts=stereo[pa];"
                  f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo[ta];[pv][pa][tv][ta]concat=n=2:v=1:a=1[vo][ao]")
        vmap, amap = ["-filter_complex", graph, "-map", "[vo]"], ["-map", "[ao]"]
    _ffmpeg(*args, *vmap, *amap, "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(dest))
    iso.unlink(missing_ok=True)
    return dest


def cut_short(video: Path, start: float, end: float, dest: Path, srt: Path | None = None) -> Path:
    """A 9:16 centre-crop cut. Superseded by post/shorts.py (native vertical layouts; the centre crop
    cut the cards in half); kept only for manual one-offs."""
    vf = "crop=ih*9/16:ih,scale=1080:1920"
    if srt:
        srt_path = str(srt).replace("\\", "\\\\").replace(":", "\\:")
        vf += f",subtitles='{srt_path}':force_style='FontName={_font()},FontSize=28,Alignment=2,MarginV=160'"
    _ffmpeg("-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", str(video), "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", str(dest))
    return dest


def run_post(video: Path, spoken_script: str, out_dir: Path, shorts: list[tuple[float, float]] | None = None,
             burn: bool = True, heard: list[Word] | None = None) -> dict:
    """Transcribe → SRT → similarity check → burned-in master → optional Shorts.

    `heard` skips transcription when the word timings are already known (post/repair.py)."""
    heard = transcribe_words(video) if heard is None else heard
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
