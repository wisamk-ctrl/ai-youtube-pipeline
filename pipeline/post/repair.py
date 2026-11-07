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
PAD = 0.06            # room tone kept either side of a clip, seconds
XFADE = 0.025         # crossfade at every splice joint, seconds (20–30 ms)
REACH = 0.12          # how far a cut may move from the middle of the gap between two words
SR = 16000            # rate of the analysis copy of the render's audio
HOP = 0.002           # energy envelope step, seconds (10 ms windows)


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
    anchors = anchor_map(words, heard, min_block=2)
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


def key(say: str) -> str:
    """Match key for a clip: the words only, so punctuation or spacing drift does not orphan it."""
    return " ".join(norm_word(w) for w in say.split() if norm_word(w))


def load_voice(reviewed_dir: Path) -> dict[str, Any] | None:
    """reviewed/<week>/repairs.yaml as {render, fix, voice: {key: url}}; None when the week has none.

    Repair is opt-in per week: a render made from a fixed script has nothing to repair, and the
    written script alone cannot tell (it still carries both spellings of a name)."""
    p = reviewed_dir / "repairs.yaml"
    if not p.exists():
        return None
    import yaml
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    voice = {key(str(k)): str(v) for k, v in (data.get("voice") or {}).items()}
    correct = {str(k): str(v) for k, v in (data.get("correct") or {}).items()}
    fixes = [str(x) for x in data.get("fix") or []] + list(correct.values())
    return {"render": str(data.get("render") or ""), "fix": fixes, "voice": voice, "correct": correct}


def apply_corrections(script: str, correct: dict[str, str]) -> str:
    """Rewrite on-air errors in the script (`correct:` in repairs.yaml), so the subtitles carry the
    corrected text; the matching speech is re-voiced because the new phrase is also a `fix`."""
    for old, new in correct.items():
        # Shot markers may sit between the words; they are kept, moved after the corrected text.
        gap = r"(?:\s+|\s*\[[^\[\]]*\]\s*)+"
        pat = re.compile(gap.join(re.escape(w) for w in old.split()))
        m = pat.search(script)
        if not m:
            log.warning("repairs.yaml correct: «%s» is not in the script; left as is", old)
            continue
        markers = " ".join(re.findall(r"\[[^\[\]]*\]", m.group(0)))
        script = script[:m.start()] + new + (f" {markers}" if markers else "") + script[m.end():]
    return script


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


def _envelope(path: Path) -> Any:
    """Short-term energy of the audio: mean power of 10 ms windows every HOP seconds (mono, SR)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    win, hop = int(0.010 * SR), int(HOP * SR)
    c = np.concatenate([[0.0], np.cumsum(x * x)])
    starts = np.arange(0, max(1, len(x) - win + 1), hop)
    return (c[np.minimum(starts + win, len(x))] - c[starts]) / win


def _frame_time(k: int) -> float:
    return k * HOP + 0.005          # centre of the 10 ms window


def quiet_cut(env: Any, heard: list[Word], t: float) -> float:
    """Where to cut near a word start `t`: the quietest point within REACH of the middle of the gap
    between the previous word's end and that word's start. `t` itself when it is no heard word's start."""
    import numpy as np
    i = next((n for n, w in enumerate(heard) if abs(w.start - t) < 1e-3), None)
    if env is None or i is None or i == 0:
        return t
    mid = (heard[i - 1].end + t) / 2
    lo = max(0, int((mid - REACH - 0.005) / HOP))
    hi = min(len(env), int((mid + REACH - 0.005) / HOP) + 1)
    if hi <= lo:
        return t
    return round(_frame_time(lo + int(np.argmin(env[lo:hi]))), 3)


def speech_db(env: Any, t0: float = 0.0, t1: float | None = None) -> float | None:
    """Active speech level in dB (as ITU-T P.56 does): the mean power of the 10 ms frames within
    25 dB of the loudest ones, so the pauses between words do not pull it down. None if silent."""
    import numpy as np
    seg = env[int(t0 / HOP):None if t1 is None else max(int(t0 / HOP) + 1, int(t1 / HOP))]
    if len(seg) == 0 or float(np.max(seg)) <= 1e-9:
        return None
    gate = max(1e-7, float(np.percentile(seg, 95)) * 10 ** -2.5)
    return float(10 * np.log10(np.mean(seg[seg >= gate])))


def room_tone_at(env: Any, seconds: float = 0.3) -> float | None:
    """Start of the render's quietest stretch that is neither digital silence nor speech (at least
    25 dB under the voice): the room tone that pads a clip. None when the render has no such pause."""
    import numpy as np
    n = int(seconds / HOP)
    voice = speech_db(env) if env is not None else None
    if voice is None or len(env) <= n:
        return None
    c = np.concatenate([[0.0], np.cumsum(env)])
    mean = (c[n:] - c[:-n]) / n
    mean[mean < 1e-9] = np.inf              # below −90 dBFS: digital silence, not a room
    k = int(np.argmin(mean))
    if not np.isfinite(mean[k]) or 10 * np.log10(mean[k]) > voice - 25:
        return None
    return round(k * HOP, 3)


_DOWNLOADS: dict[str, Path] = {}


def _clip(url: str, dest: Path) -> Path:
    """Download a clip and trim its leading and trailing silence.

    `<url>#t=<start>,<end>` takes that stretch of a longer recording: every phrase of a week can
    come from one speech call (one credit minimum per call), split by its word timestamps."""
    if url.startswith("silence:"):   # a dropped gloss: the span becomes a short natural pause
        _run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
             "anullsrc=r=48000:cl=stereo", "-t", url.partition(":")[2] or "0.15", str(dest))
        return dest
    base, _, frag = url.partition("#t=")
    raw = _DOWNLOADS.get(base)
    if raw is None or not raw.exists():
        raw = dest.with_suffix(".src")
        req = urllib.request.Request(base, headers={"User-Agent": "ai-youtube-pipeline"})
        with urllib.request.urlopen(req, timeout=120) as r:
            raw.write_bytes(r.read())
        _DOWNLOADS[base] = raw
    cut: list[str] = []
    if frag:
        a, _, b = frag.partition(",")
        cut = ["-ss", f"{float(a):.3f}"] + (["-to", f"{float(b):.3f}"] if b else [])
    trim = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
    _run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), *cut, "-af", trim,
         "-ar", "48000", "-ac", "2", str(dest))
    return dest


def apply(video: Path, repairs: list[Repair], heard: list[Word], out_dir: Path, fps: int = 30
          ) -> tuple[Path, list[tuple[float, float]], list[Word]]:
    """Splice the clips in. Returns (repaired video, spans to hide the face, heard words retimed).

    Each cut moves to the quietest point of the gap between two words (`quiet_cut`); every joint is
    a short crossfade (XFADE) that keeps the total length exact; a clip's padding is the render's
    own room tone, never digital silence; a clip is matched to the render's speech level (`speech_db`)."""
    todo = sorted((r for r in repairs if r.audio), key=lambda r: r.start)
    if not todo:
        return video, [], heard
    work = out_dir / "repair"
    work.mkdir(parents=True, exist_ok=True)
    clips, kept = [], []
    for n, r in enumerate(todo):
        try:     # one expired or broken clip must not sink the edit: that phrase is left as it was
            c = _clip(r.audio, work / f"clip_{n:02d}.wav")
            length = _duration(c) + 2 * PAD
        except Exception as exc:  # noqa: BLE001
            log.warning("Repair clip for «%s» unusable (%s); left as rendered", r.say, exc)
            r.audio = ""
            continue
        clips.append((c, length))
        kept.append(r)
    todo = kept
    if not todo:
        return video, [], heard
    total = _duration(video)
    try:
        env = _envelope(video)
    except Exception as exc:  # noqa: BLE001 — without the analysis the cuts stay on the word starts
        log.warning("Repair: audio analysis failed (%s); cutting on word starts", exc)
        env = None
    cuts, cursor = [], 0.0
    for r in todo:
        a, b = quiet_cut(env, heard, r.start), quiet_cut(env, heard, r.end)
        if not (cursor + 0.05 < a < r.start + REACH + 0.01 and a + 0.1 < b):
            a, b = r.start, r.end
        cuts.append((a, b))
        cursor = b
    tone_at = room_tone_at(env)
    tone = None
    if tone_at is not None:
        tone = work / "room_tone.wav"
        _run("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{tone_at:.3f}", "-t", "0.3", "-i", str(video),
             "-vn", "-ar", "48000", "-ac", "2", str(tone))
    gains = []
    for r, (a, b), (c, _) in zip(todo, cuts, clips):
        if r.audio.startswith("silence:"):
            gains.append(0.0)
            continue
        ctx = max(3.0, b - a)                        # the voice around the repair, pauses left out
        mine = speech_db(env, max(0.0, (a + b - ctx) / 2), (a + b + ctx) / 2) if env is not None else None
        theirs = speech_db(_envelope(c)) if mine is not None else None
        gain = mine - theirs if mine is not None and theirs is not None else _mean_db(video, a, b - a) - _mean_db(c)
        gains.append(max(-12.0, min(12.0, gain)))
    norm = "aformat=sample_rates=48000:channel_layouts=stereo"
    pieces: list[tuple[str, Any]] = []               # ("src", (a, b)) or ("clip", n), in order
    cursor = 0.0
    for n, (a, b) in enumerate(cuts):
        if a > cursor + 1e-3:
            pieces.append(("src", (cursor, a)))
        pieces.append(("clip", n))
        cursor = b
    if cursor < total - 1e-3:
        pieces.append(("src", (cursor, None)))
    half = XFADE / 2      # each internal joint borrows half a crossfade from both sides: length stays exact
    parts, vlab, alab, hides, shifts = [], [], [], [], []
    tone_len = [0.0] * len(clips)                   # one looped room-tone input per clip, as long as its piece
    offset = 0.0
    for p, (kind, what) in enumerate(pieces):
        left = half if p > 0 else 0.0
        right = half if p < len(pieces) - 1 else 0.0
        if kind == "src":
            a, b = what
            end_v = f":end={b:.3f}" if b is not None else ""
            end_a = f":end={b + right:.3f}" if b is not None else ""
            parts.append(f"[0:v]trim=start={a:.3f}{end_v},setpts=PTS-STARTPTS,fps={fps}[v{p}];"
                         f"[0:a]atrim=start={a - left:.3f}{end_a},asetpts=PTS-STARTPTS,{norm}[a{p}];")
        else:
            n = what
            r, (a, b), (c, length), gain = todo[n], cuts[n], clips[n], gains[n]
            span, alen = b - a, length + left + right
            parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=(PTS-STARTPTS)*{length / span:.5f},"
                         f"fps={fps},tpad=stop_mode=clone:stop_duration=1,trim=duration={length:.3f}[v{p}];"
                         f"[{n + 1}:a]{norm},volume={gain:.2f}dB,adelay={int(round((PAD + left) * 1000))}:all=1,apad,"
                         f"atrim=duration={alen:.3f},asetpts=PTS-STARTPTS" + ("[c%d];" % p if tone else f"[a{p}];"))
            if tone:
                tone_len[n] = alen
                parts.append(f"[{len(clips) + 1 + n}:a]{norm},atrim=duration={alen:.3f},asetpts=PTS-STARTPTS[t{p}];"
                             f"[c{p}][t{p}]amix=inputs=2:normalize=0:duration=first[a{p}];")
            new_start = a + offset
            hides.append((round(new_start, 3), round(new_start + length, 3)))
            shifts.append((r.start, r.end, offset, length - span))
            offset += length - span
        vlab.append(f"[v{p}]")
        alab.append(f"[a{p}]")
    chain, prev = [], alab[0]
    for p in range(1, len(alab)):
        out_l = "[a]" if p == len(alab) - 1 else f"[x{p}]"
        chain.append(f"{prev}{alab[p]}acrossfade=d={XFADE:.3f}:c1=qsin:c2=qsin{out_l};")
        prev = out_l
    if len(alab) == 1:
        chain.append(f"{alab[0]}anull[a];")
    graph = "".join(parts) + "".join(chain) + "".join(vlab) + f"concat=n={len(vlab)}:v=1:a=0[v]"
    dest = out_dir / "talking_head.repaired.mp4"
    inputs = ["-i", str(video)] + [x for c, _ in clips for x in ("-i", str(c))]
    if tone:
        inputs += [x for t in tone_len for x in ("-stream_loop", "-1", "-t", f"{t + 0.1:.3f}", "-i", str(tone))]
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
