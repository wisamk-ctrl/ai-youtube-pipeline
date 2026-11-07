"""
Speech repair on a finished render, without re-rendering the avatar.

Some faults are in the voice, not the picture: a name said twice («أوبن إيه آي OpenAI»), an
English gloss read aloud, a name the voice mispronounces (G42, Claude), a word misread from its
vowel marks. Each such phrase is re-voiced with the presenter's cloned voice and spliced in:

1. `find()` marks every faulty phrase in the approved script and widens it to the nearest words
   Whisper heard cleanly on both sides, so the splice points sit on reliable word timings.
   (Whisper often merges a doubled name into one word, so cutting by its timings is unreliable;
   replacing the whole span between two clean anchors is not.)
2. The replacement clips are made outside CI (the HeyGen connector's speech tool, which uses plan
   credits) and listed in reviewed/<week>/repairs.yaml as `voice: {"<text said>": <audio URL>}`.
   `fix:` in the same file adds phrases by hand (e.g. «عن بُعد», misread from its harakat).
3. `apply()` swaps each span's audio for its clip, retimes the picture under it, and returns the
   spans the edit must cover with a visual: the lips no longer match the voice there.

Phrases with no clip yet are listed in repairs.md and left as they are.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pipeline.post.subtitles import Word, anchor_map, norm_word
from pipeline.script_format import _GLOSS, _pronunciation, _same_name_words, speakable

log = logging.getLogger(__name__)

_LATIN = re.compile(r"[A-Za-z]")
_ARABIC = re.compile(r"[؀-ۿ]")
PAD = 0.06            # silence kept either side of a clip, seconds


@dataclass
class Repair:
    words: tuple[int, int]       # script word range [k, m) that is re-voiced
    start: float                 # seconds in the render
    end: float
    phrase: str                  # as written
    say: str                     # what the clip must say (speakable form)
    why: str
    audio: str = ""              # clip URL, once made


def _core(tok: str) -> str:
    return re.sub(r"^[^\w(]+|[^\w)]+$", "", tok)


def _targets(words: list[str], pron: dict[str, str], fixes: list[str]) -> list[tuple[int, int, str]]:
    """Script word ranges [i, j] (inclusive) that the voice gets wrong."""
    out: list[tuple[int, int, str]] = []
    n = len(words)
    i = 0
    while i < n:
        tok = words[i]
        if tok.startswith("(") and _LATIN.search(tok) and not _ARABIC.search(tok):     # English gloss
            j = i
            while j < n - 1 and ")" not in words[j]:
                j += 1
            out.append((i, j, "English gloss read aloud"))
            i = j + 1
            continue
        if _LATIN.search(tok) and not _ARABIC.search(tok) and i > 0:                   # name said twice
            j = i
            while j + 1 < n and _LATIN.search(words[j + 1]) and not _ARABIC.search(words[j + 1]) \
                    and not words[j].endswith((".", "،", ",")):
                j += 1
            ar = []
            for w in reversed(words[max(0, i - 4):i]):
                if not _ARABIC.search(w) or _LATIN.search(w):
                    break
                ar.insert(0, _core(w))
            k = _same_name_words(ar, " ".join(_core(w) for w in words[i:j + 1])) if ar else 0
            if k:
                out.append((i - k, j, "name said twice"))
                i = j + 1
                continue
        i += 1
    latin_part = [re.sub(r"^[\u0600-\u06FF\u0640]+", "", _core(w)) for w in words]   # «وG42» → «G42»
    for key in pron:                                                                  # mispronounced
        kt = key.split()
        for i in range(n - len(kt) + 1):
            if latin_part[i:i + len(kt)] == kt:
                out.append((i, i + len(kt) - 1, f"mispronounced: {key}"))
    for phrase in fixes:                                                              # by hand
        pt = [norm_word(w) for w in phrase.split()]
        for i in range(n - len(pt) + 1):
            if [norm_word(w) for w in words[i:i + len(pt)]] == pt:
                out.append((i, i + len(pt) - 1, "misread (listed by hand)"))
    return sorted(set(out))


def find(spoken_script: str, heard: list[Word], cfg: dict[str, Any] | None = None,
         fixes: list[str] | None = None, pron: dict[str, str] | None = None) -> tuple[list[Repair], list[str]]:
    """Every faulty phrase, widened to clean anchors. Returns (repairs, skipped notes)."""
    words = spoken_script.split()
    pron = _pronunciation() if pron is None else pron
    anchors = anchor_map(words, heard)
    reach = int(((cfg or {}).get("post", {}).get("repair", {}) or {}).get("anchor_reach", 3))
    spans: list[list[Any]] = []
    for i, j, why in _targets(words, pron, fixes or []):
        if spans and i <= spans[-1][1] + 1:          # overlapping or touching: one splice
            spans[-1][1] = max(spans[-1][1], j)
            spans[-1][2] += f"; {why}"
        else:
            spans.append([i, j, why])
    repairs: list[Repair] = []
    skipped: list[str] = []
    for i, j, why in spans:
        if (i - 1) in anchors and (j + 1) in anchors and anchors[j + 1] == anchors[i - 1] + 1:
            skipped.append(f"«{' '.join(words[i:j + 1])}» ({why}): not spoken in the render")
            continue
        k = next((x for x in range(i, max(-1, i - reach - 1), -1) if x in anchors), None)
        m = next((x for x in range(j + 1, min(len(words), j + reach + 2)) if x in anchors), None)
        phrase = " ".join(words[i:j + 1])
        if k is None or m is None or anchors[k] >= anchors[m]:
            skipped.append(f"«{phrase}» ({why}): no cleanly heard word near enough on both sides")
            continue
        if repairs and k < repairs[-1].words[1]:      # widened into the previous splice: join them
            prev = repairs.pop()
            k = prev.words[0]
            why = f"{prev.why}; {why}"
        start, end = heard[anchors[k]].start, heard[anchors[m]].start
        text = " ".join(words[k:m])
        if not 0.3 <= end - start <= 12:
            skipped.append(f"«{text}» ({why}): span of {end - start:.1f}s looks wrong")
            continue
        say = re.sub(r"\s+", " ", _GLOSS.sub("", speakable(text, pron))).strip()
        repairs.append(Repair((k, m), round(start, 3), round(end, 3), text, say, why))
    return repairs, skipped


def load_voice(reviewed_dir: Path) -> tuple[dict[str, str], list[str]]:
    """(clip URL per text said, hand-listed phrases) from reviewed/<week>/repairs.yaml."""
    p = reviewed_dir / "repairs.yaml"
    if not p.exists():
        return {}, []
    import yaml
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    voice = {re.sub(r"\s+", " ", str(k)).strip(): str(v) for k, v in (data.get("voice") or {}).items()}
    return voice, [str(x) for x in data.get("fix") or []]


def report_md(repairs: list[Repair], skipped: list[str]) -> str:
    def ts(x: float) -> str:
        return f"{int(x // 60)}:{int(x % 60):02d}"
    done = sum(1 for r in repairs if r.audio)
    lines = [f"## Speech repairs\n\n{done} of {len(repairs)} phrases re-voiced"
             + (" · the rest need a clip in reviewed/<week>/repairs.yaml" if done < len(repairs) else ""), ""]
    for r in repairs:
        lines.append(f"- {ts(r.start)} {'✅' if r.audio else '⏳'} «{r.phrase}» → say «{r.say}» ({r.why})")
    if skipped:
        lines += ["", "Left as they are:"] + [f"- {s}" for s in skipped]
    return "\n".join(lines) + "\n"


# ── Applying the clips ────────────────────────────────────────────────────────

def _run(*args: str) -> str:
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{args[0]} failed: {r.stderr[-1500:]}")
    return r.stderr + r.stdout


def _duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def _mean_db(path: Path, start: float | None = None, length: float | None = None) -> float:
    cut = ["-ss", f"{start:.3f}", "-t", f"{length:.3f}"] if start is not None else []
    log_txt = _run("ffmpeg", "-hide_banner", *cut, "-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-")
    m = re.search(r"mean_volume:\s*(-?[\d.]+) dB", log_txt)
    return float(m.group(1)) if m else -20.0


def _clip(url: str, dest: Path) -> Path:
    """Download a clip and trim its leading and trailing silence."""
    raw = dest.with_suffix(".src")
    req = urllib.request.Request(url, headers={"User-Agent": "ai-youtube-pipeline"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw.write_bytes(r.read())
    trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    _run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), "-af", trim, "-ar", "48000", "-ac", "2", str(dest))
    return dest


def apply(video: Path, repairs: list[Repair], heard: list[Word], out_dir: Path, fps: int = 30
          ) -> tuple[Path, list[tuple[float, float]], list[Word]]:
    """Splice the clips in. Returns (repaired video, spans to hide the face, heard words retimed)."""
    todo = sorted((r for r in repairs if r.audio), key=lambda r: r.start)
    if not todo:
        return video, [], heard
    work = out_dir / "repair"
    work.mkdir(parents=True, exist_ok=True)
    clips = []
    for n, r in enumerate(todo):
        c = _clip(r.audio, work / f"clip_{n:02d}.wav")
        length = _duration(c) + 2 * PAD
        gain = _mean_db(video, r.start, r.end - r.start) - _mean_db(c)
        clips.append((c, length, max(-12.0, min(12.0, gain))))
    total = _duration(video)
    norm = "aformat=sample_rates=48000:channel_layouts=stereo"
    parts, labels, hides, shifts = [], [], [], []
    cursor, offset = 0.0, 0.0
    for n, (r, (c, length, gain)) in enumerate(zip(todo, clips)):
        if r.start > cursor + 1e-3:   # untouched stretch before this repair
            parts.append(f"[0:v]trim=start={cursor:.3f}:end={r.start:.3f},setpts=PTS-STARTPTS,fps={fps}[v{n}k];"
                         f"[0:a]atrim=start={cursor:.3f}:end={r.start:.3f},asetpts=PTS-STARTPTS,{norm},"
                         f"afade=t=in:d=0.01,afade=t=out:st={max(0.0, r.start - cursor - 0.01):.3f}:d=0.01[a{n}k];")
            labels.append(f"[v{n}k][a{n}k]")
        span = r.end - r.start
        parts.append(f"[0:v]trim=start={r.start:.3f}:end={r.end:.3f},setpts=(PTS-STARTPTS)*{length / span:.5f},"
                     f"fps={fps},tpad=stop_mode=clone:stop_duration=1,trim=duration={length:.3f}[v{n}r];"
                     f"[{n + 1}:a]{norm},volume={gain:.2f}dB,adelay={int(PAD * 1000)}:all=1,apad,"
                     f"atrim=duration={length:.3f},asetpts=PTS-STARTPTS[a{n}r];")
        labels.append(f"[v{n}r][a{n}r]")
        new_start = r.start + offset
        hides.append((round(new_start, 3), round(new_start + length, 3)))
        shifts.append((r.start, r.end, offset, length - span))
        offset += length - span
        cursor = r.end
    if cursor < total - 1e-3:
        parts.append(f"[0:v]trim=start={cursor:.3f},setpts=PTS-STARTPTS,fps={fps}[vend];"
                     f"[0:a]atrim=start={cursor:.3f},asetpts=PTS-STARTPTS,{norm},afade=t=in:d=0.01[aend];")
        labels.append("[vend][aend]")
    graph = "".join(parts) + "".join(labels) + f"concat=n={len(labels)}:v=1:a=1[v][a]"
    dest = out_dir / "talking_head.repaired.mp4"
    inputs = ["-i", str(video)] + [x for c, _, _ in clips for x in ("-i", str(c))]
    _run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs, "-filter_complex", graph,
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(dest))
    retimed = retime(heard, shifts)
    (out_dir / "repairs.json").write_text(json.dumps([asdict(r) for r in repairs], ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    log.info("Speech repair: %d phrases re-voiced, video %+.1fs", len(todo), offset)
    return dest, hides, retimed


def retime(heard: list[Word], shifts: list[tuple[float, float, float, float]]) -> list[Word]:
    """Move word timings onto the repaired timeline; words inside a replaced span are dropped."""
    out = []
    for w in heard:
        offset, inside = 0.0, False
        for a, b, before, delta in shifts:
            if w.end > a and w.start < b:
                inside = True
                break
            if w.start >= b:
                offset = before + delta
        if not inside:
            out.append(Word(round(w.start + offset, 3), round(w.end + offset, 3), w.word))
    return out
