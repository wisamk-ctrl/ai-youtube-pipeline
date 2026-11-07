"""
The final audio pass (review 2026-11-07, Tier 1 #9): the W45 master measured −19.6 LUFS and a dry
voice, so it played ~5 dB quieter than the videos around it.

    voice (the edit's track) ─┬──────────────────────────────┐
                              └ sidechain ─► music bed ducked ┴► mix ─► [sting spliced in] ─► loudnorm ×2 ─► wav

- Music bed: synthesised here (a calm D-minor pad with a soft pulse), never licensed third-party
  music (founder). Fixed and deterministic: a 32-second loop that tiles without a seam.
- Whoosh: a short swept-noise swish (also synthesised) peaking on each section cut.
- Sting: assets/intro_sting.mp4 (our own code-rendered sting, sting/) spliced in after the cold
  open; its audio is levelled to the voice. The picture side of the splice is in subtitles.burn_in.
- Loudness: two-pass loudnorm, measured values fed back so the second pass is linear.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import wave
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger(__name__)

RATE = 48000
LOOP_SECONDS = 32                     # 4 chords × 8 s; every frequency is a multiple of 1/32 Hz
_D3 = 146.83
CHORDS = [                            # semitones above D3: Dm9, B♭maj7, Fmaj7/C, Am7 (D minor)
    [0, 3, 7, 10, 14],
    [-4, 0, 3, 7],
    [3, 7, 10, 14],
    [-5, 2, 7, 10],
]


def _ff(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y", *args], check=True, capture_output=True, text=True)


def _periodic(f: float) -> float:
    """Round a frequency to a whole number of cycles per loop, so the loop has no seam."""
    return round(f * LOOP_SECONDS) / LOOP_SECONDS


def _write_wav(dest: Path, stereo: np.ndarray) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(dest), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    return dest


def music_loop(dest: Path) -> Path:
    """One 32 s loop of the bed: a slow pad (detuned sines, stereo) and a soft pulse on the beat."""
    t = np.arange(LOOP_SECONDS * RATE) / RATE
    left, right = np.zeros_like(t), np.zeros_like(t)
    seg = LOOP_SECONDS / len(CHORDS)
    xf = 2.0                                               # crossfade between chords, seconds
    for i, chord in enumerate(CHORDS):
        d = (t - i * seg) % LOOP_SECONDS
        env = np.where(d < xf, np.sin(np.pi / 2 * d / xf) ** 2,
                       np.where(d < seg, 1.0, np.where(d < seg + xf, np.cos(np.pi / 2 * (d - seg) / xf) ** 2, 0.0)))
        for k, semi in enumerate(chord):
            f = _D3 * 2 ** (semi / 12)
            amp = 0.16 / (1 + 0.25 * k)
            breath = 0.75 + 0.25 * np.sin(2 * np.pi * t * (k + 1) / LOOP_SECONDS + k)   # slow swell, periodic
            for ch, detune in ((left, 0.0), (right, 3 / LOOP_SECONDS)):
                ff = _periodic(f) + detune
                ch += env * amp * breath * (np.sin(2 * np.pi * ff * t) + 0.18 * np.sin(2 * np.pi * 2 * ff * t))
        # The pulse: a soft high blip on every beat (90 bpm → 48 beats a loop), the chord's root two octaves up.
        root = _periodic(_D3 * 2 ** (chord[0] / 12) * 4)
        beat = 60 / 90
        phase = (t - i * seg) % LOOP_SECONDS
        inside = phase < seg
        local = phase % beat
        blip = np.exp(-local / 0.12) * np.sin(2 * np.pi * root * t) * 0.05 * inside
        left += blip * 0.8
        right += blip
        sub = np.exp(-local / 0.35) * np.sin(2 * np.pi * _periodic(_D3 / 2 * 2 ** (chord[0] / 12)) * t) * 0.12 * inside
        sub *= (np.floor(phase / beat) % 2 == 0)              # every other beat
        left += sub
        right += sub
    stereo = np.stack([left, right], axis=1)
    stereo *= 0.5 / np.max(np.abs(stereo))                 # −6 dBFS peak
    return _write_wav(dest, stereo)


WHOOSH_RMS = 0.1                      # −20 dBFS


def whoosh(dest: Path, seconds: float = 0.9) -> Path:
    """A swept-noise swish that rises to its peak at 70 % and falls off (deterministic noise seed)."""
    n = int(seconds * RATE)
    rng = np.random.default_rng(45)
    noise = rng.standard_normal((n, 2))
    # A one-pole low-pass whose cutoff sweeps up then down: the "air moving past" sound.
    t = np.arange(n) / n
    peak = 0.7
    sweep = np.where(t < peak, t / peak, 1 - (t - peak) / (1 - peak))
    cutoff = 300 + 5000 * sweep ** 2
    a = np.exp(-2 * np.pi * cutoff / RATE)
    out = np.zeros_like(noise)
    y = np.zeros(2)
    for i in range(n):
        y = a[i] * y + (1 - a[i]) * noise[i]
        out[i] = y
    out *= (sweep ** 1.5)[:, None]
    out *= WHOOSH_RMS / np.sqrt(np.mean(out ** 2))       # a known level (too short for loudnorm to measure)
    return _write_wav(dest, out)


def measure(path: Path, start: float | None = None, end: float | None = None) -> dict[str, float]:
    """Pass 1 of loudnorm: integrated loudness, true peak, range and threshold of the file."""
    trim = ["-ss", f"{start:.3f}"] if start is not None else []
    trim += ["-to", f"{end:.3f}"] if end is not None else []
    r = _ff(*trim, "-i", str(path), "-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json", "-f", "null", "-")
    stats = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    return {k: float(stats[k]) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}


def normalise(src: Path, dest: Path, lufs: float = -14.0, tp: float = -1.5, lra: float = 7.0) -> Path:
    """Two-pass loudnorm: measure, then apply with the measured values (linear when it can be)."""
    m = measure(src)
    af = (f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
          f"aresample={RATE}")
    _ff("-i", str(src), "-vn", "-af", af, "-c:a", "pcm_s16le", str(dest))
    log.info("Loudness %.1f LUFS → %.1f LUFS target (TP %.1f dBTP)", m["input_i"], lufs, m["input_tp"])
    return dest


def silence_cut(video: Path, around: float, before: float = 1.5, after: float = 0.3) -> float:
    """The middle of the pause nearest `around` (the next sentence's first word), else just before it."""
    a = max(0.0, around - before)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{a:.3f}", "-t", f"{before + after:.3f}", "-i", str(video),
                        "-vn", "-af", "silencedetect=noise=-35dB:d=0.12", "-f", "null", "-"], capture_output=True, text=True)
    starts = [a + float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = [a + float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    gaps = [(s, e) for s, e in zip(starts, ends + [around + after] * (len(starts) - len(ends)))]
    if not gaps:
        return max(0.0, around - 0.12)
    s, e = min(gaps, key=lambda g: abs((g[0] + g[1]) / 2 - around))
    return max(0.0, (s + e) / 2)


def section_times(script: str, srt: Path | None, wpm: int) -> list[float]:
    """When each [Section] after the first is heard: the start of the caption that begins with the
    section's first spoken words (the estimate from words-per-minute when no caption matches)."""
    from pipeline.post.overlays import _srt_index
    from pipeline.script_format import extract_cues, spoken_text
    words = spoken_text(script).split()
    idx = _srt_index(srt)
    out = []
    for c in extract_cues(script, wpm):
        if c.kind != "section" or c.at_word == 0:
            continue
        probe = " ".join(words[c.at_word:c.at_word + 3])
        hits = [t for t, text in idx if probe and text.startswith(probe)]
        out.append(min(hits, key=lambda t: abs(t - c.at_seconds)) if hits else c.at_seconds)
    return out


def sting_plan(cfg: dict[str, Any], script: str, srt: Path | None, video: Path, root: Path) -> tuple[float, Path] | None:
    """(cut time, sting video): the sting goes after the cold open, i.e. at the first [Section] after it."""
    s = cfg.get("post", {}).get("sting", {})
    path = root / s.get("path", "assets/intro_sting.mp4")
    if not s.get("enabled") or not path.exists():
        return None
    times = section_times(script, srt, cfg["scripting"]["words_per_minute"])
    if not times or not srt:
        log.warning("Sting skipped: no timed [Section] after the cold open")
        return None
    return silence_cut(video, times[0]), path


def master(video: Path, dest: Path, cfg: dict[str, Any], work: Path, insert: tuple[float, Path] | None = None,
           cuts: list[float] | None = None) -> Path | None:
    """The episode's final audio as a 48 kHz wav: voice + ducked bed (+ whooshes) (+ sting), loudnormed.

    Times in `cuts` and `insert` are on the edit's own timeline (before the sting is spliced in)."""
    a = cfg.get("post", {}).get("audio", {})
    if not a.get("enabled", True):
        return None
    from pipeline.post.edit import duration
    work.mkdir(parents=True, exist_ok=True)
    dur = duration(video)
    voice = measure(video)
    inputs = ["-i", str(video)]
    count = 1                                              # ffmpeg input index of the next -i
    graph = ["[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[vo][sc]"]
    mix = ["[vo]"]
    music = str(a.get("music", "generated"))
    if music != "none":
        bed = music_loop(work / "bed_loop.wav") if music == "generated" else Path(music)
        bed_i = measure(bed)["input_i"]
        # Ducking takes ~6 dB off the bed under speech; so set it ~6 dB above where it should sit.
        gain = voice["input_i"] + float(a.get("music_db", -24)) + 6 - bed_i
        inputs += ["-stream_loop", "-1", "-i", str(bed)]
        count += 1
        graph.append(f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{dur:.3f},volume={gain:.2f}dB,"
                     f"afade=t=in:d=3,afade=t=out:st={max(0.0, dur - 4):.3f}:d=4[bed]")
        graph.append("[bed][sc]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=500:knee=4[duck]")
        mix.append("[duck]")
    else:
        graph.append("[sc]anullsink")
    if a.get("whoosh", True) and cuts:
        sw = whoosh(work / "whoosh.wav")
        sw_gain = voice["input_i"] - 16 + 20                 # ~16 dB under the voice
        for k, t in enumerate(c for c in cuts if not insert or abs(c - insert[0]) > 1.0):
            n, count = count, count + 1
            inputs += ["-i", str(sw)]
            ms = max(0, int((t - 0.63) * 1000))           # the swish peaks on the cut
            graph.append(f"[{n}:a]volume={sw_gain:.2f}dB,adelay={ms}:all=1[w{k}]")
            mix.append(f"[w{k}]")
    graph.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first[prog]")
    out = "[prog]"
    if insert:
        at, sting = insert
        n, count = count, count + 1
        inputs += ["-i", str(sting)]
        st_gain = voice["input_i"] - 2 - measure(sting)["input_i"]
        graph.append(f"[prog]asplit=2[p1][p2];[p1]atrim=0:{at:.3f},afade=t=out:st={max(0.0, at - 0.08):.3f}:d=0.08[a1];"
                     f"[p2]atrim=start={at:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.08[a2];"
                     f"[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={st_gain:.2f}dB[st];"
                     f"[a1][st][a2]concat=n=3:v=0:a=1[spliced]")
        out = "[spliced]"
    raw = work / "mix_raw.wav"
    _ff(*inputs, "-filter_complex", ";".join(graph), "-map", out, "-c:a", "pcm_s24le", "-ar", str(RATE), str(raw))
    return normalise(raw, dest, float(a.get("loudness_lufs", -14)), float(a.get("true_peak", -1.5)), float(a.get("lra", 7)))


def shift_srt(srt: Path, at: float, by: float, dest: Path) -> Path:
    """The captions on the final timeline: every caption starting at or after `at` moves by `by` seconds."""
    def ts(s: str) -> float:
        h, m, rest = s.split(":")
        return int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))

    def fmt(x: float) -> str:
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    def move(m: re.Match) -> str:
        a, b = ts(m[1]), ts(m[2])
        d = by if a >= at - 1e-3 else 0.0
        return f"{fmt(a + d)} --> {fmt(min(b, at) if d == 0 and b > at else b + d)}"

    text = re.sub(r"(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)", move, srt.read_text(encoding="utf-8"))
    dest.write_text(text, encoding="utf-8")
    return dest


def duration_of(path: Path) -> float:
    from pipeline.post.edit import duration
    return duration(path)
