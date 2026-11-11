"""
The founder's own recording (founder decision 2026-11-08): clean it before it becomes the episode.

1. Voice chain: high-pass, mud cut, presence and air lift, de-esser, gentle compression (no denoise:
   it muffled the W45 read).
2. Retakes: the read is split at pauses; a stretch whose opening words come back in one of the next
   two stretches is a retake ("pause two seconds and say the sentence again"), so the earlier one is
   cut and the last take kept.
3. Stumbles: the same 2-4 words said twice back to back are cut to one; so is any phrase listed in
   voice.yaml `cut_repeats:` (alternative spellings joined with `|`); `cut:` spans ("3:19.4-3:21.0",
   recording time) are cut as given, for anything the recogniser hides.
4. Pauses: any pause longer than `max_pause` is shortened to it.

Writes the cleaned wav and a markdown report (what was cut, the phrases not found, and the timed
transcript of the recording) for the review issue.
"""

from __future__ import annotations

import logging
import subprocess
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from pipeline.post.subtitles import Word, norm_word, transcribe_words

log = logging.getLogger(__name__)

# No noise reduction: the W45 room measured a -71 dB floor, and afftdn dulled the voice ("muffled",
# founder 2026-11-09). A phone memo is dark (3-6 kHz ~-28 dB under the total), so: mud cut, presence
# and air lift, de-esser, gentle compression.
VOICE_CHAIN = ("highpass=f=80,equalizer=f=220:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=4,"
               "highshelf=f=7500:g=4,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=180:makeup=3,"
               "deesser=i=0.4,loudnorm=I=-16:TP=-1.5:LRA=9")


def _ff(*args: str) -> None:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {r.stderr[-1500:]}")


def stretches(words: list[Word], gap: float = 0.6) -> list[list[Word]]:
    out: list[list[Word]] = []
    for w in words:
        if out and w.start - out[-1][-1].end < gap:
            out[-1].append(w)
        else:
            out.append([w])
    return out


def _opening(s: list[Word], n: int = 4) -> str:
    return " ".join(norm_word(w.word) for w in s[:n])


def retakes(parts: list[list[Word]], look: int = 2) -> set[int]:
    """Indexes of stretches that are abandoned takes: their first words are said again within the
    next `look` stretches, and they are not longer than that later take (a full sentence is not
    dropped for a shorter echo of its start)."""
    drop: set[int] = set()
    for i, a in enumerate(parts):
        if len(a) < 2:
            continue
        for j in range(i + 1, min(len(parts), i + 1 + look)):
            b = parts[j]
            n = min(4, len(a), len(b))
            if n >= 2 and SequenceMatcher(None, _opening(a, n), _opening(b, n)).ratio() >= 0.8 and len(a) <= len(b) + 2:
                drop.add(i)
                break
    return drop


def back_to_back(words: list[Word]) -> list[tuple[float, float, str]]:
    """The same 2-4 words twice in a row: cut from the first saying's start to the second's."""
    hw = [norm_word(w.word) for w in words]
    cuts, taken = [], -1
    for k in range(len(hw)):
        if k <= taken:
            continue
        for n in (4, 3, 2):
            if k + 2 * n <= len(hw) and all(hw[k:k + n]) and hw[k:k + n] == hw[k + n:k + 2 * n]:
                cuts.append((words[k].start, words[k + n].start, " ".join(w.word.strip() for w in words[k:k + n])))
                taken = k + n - 1
                break
    return cuts


def repeat_cuts(words: list[Word], phrases: list[str], within: float = 4.0
                ) -> tuple[list[tuple[float, float, str]], list[str]]:
    """Spans to cut where a listed phrase is said twice in a row (a stumble with no long pause):
    from the first saying's start to the second's start, so the second (complete) one stays.
    A phrase may list spellings as "a | b"; any two sayings in any spelling count. Returns
    (cuts, phrases not found)."""
    heard = [norm_word(w.word) for w in words]
    cuts, missed = [], []
    for phrase in phrases:
        starts: set[int] = set()   # the first word: a stumble is often cut off after it
        full: set[int] = set()     # the first two words: the complete saying that stays
        for alt in phrase.split("|"):
            toks = [norm_word(t) for t in alt.split() if norm_word(t)][:2]
            if not toks:
                continue
            for i in range(len(heard)):
                if SequenceMatcher(None, heard[i], toks[0]).ratio() >= 0.75:
                    starts.add(i)
                    if i + len(toks) <= len(heard) and all(
                            SequenceMatcher(None, heard[i + k], toks[k]).ratio() >= 0.75 for k in range(len(toks))):
                        full.add(i)
        found = False
        order = sorted(starts)
        for a, b in zip(order, order[1:]):
            if b in full and 0 < words[b].start - words[a].start <= within:
                cuts.append((words[a].start, words[b].start, phrase.strip()))
                found = True
                break
        if not found:
            missed.append(phrase.strip())
    return cuts, missed


def parse_spans(spans: list[str]) -> list[tuple[float, float]]:
    """["3:19.4-3:21.0", "200.5-201"] → [(199.4, 201.0), (200.5, 201.0)]."""
    def sec(x: str) -> float:
        parts = [float(p) for p in x.strip().split(":")]
        return sum(v * 60 ** i for i, v in enumerate(reversed(parts)))
    out = []
    for s in spans:
        a, b = str(s).split("-", 1)
        a_s, b_s = sec(a), sec(b)
        if b_s <= a_s:
            raise ValueError(f"voice.yaml cut: {s!r} ends before it starts")
        out.append((a_s, b_s))
    return out


def _minus(spans: list[tuple[float, float]], cuts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    out = []
    for a, b in spans:
        pieces = [(a, b)]
        for c, d in cuts:
            nxt = []
            for x, y in pieces:
                if d <= x or c >= y:
                    nxt.append((x, y))
                    continue
                if c > x:
                    nxt.append((x, c))
                if d < y:
                    nxt.append((d, y))
            pieces = nxt
        out += [p for p in pieces if p[1] - p[0] > 0.05]
    return out


def clean(src: Path, dest: Path, cfg: dict[str, Any] | None = None,
          cut_repeats: list[str] | None = None, cut: list[str] | None = None) -> tuple[Path, str]:
    """src (any audio) → dest wav, cleaned. Returns (dest, markdown report)."""
    o = ((cfg or {}).get("video", {}).get("own_voice") or {})
    max_pause, pad = float(o.get("max_pause", 0.5)), 0.08
    polished = dest.with_name(dest.stem + ".polished.wav")
    _ff("-i", str(src), "-af", VOICE_CHAIN, "-ar", "48000", "-ac", "2", str(polished))
    words = transcribe_words(polished)
    parts = stretches(words)
    drop = retakes(parts) if o.get("cut_retakes", True) else set()
    keep = [(max(0.0, p[0].start - pad), p[-1].end + pad) for i, p in enumerate(parts) if i not in drop]
    stumbles = back_to_back(words) if o.get("cut_back_to_back", True) else []
    listed, missed = repeat_cuts(words, cut_repeats or [])
    stumbles += [c for c in listed if not any(abs(c[0] - s[0]) < 1.0 for s in stumbles)]
    spans = parse_spans(cut or [])
    keep = _minus(keep, [(a, b) for a, b, _ in stumbles] + spans)
    if not keep:
        raise RuntimeError("own voice: no speech found in the recording")
    # Join the kept stretches, each pause capped at max_pause, 15 ms fades at every joint.
    pieces, graph = [], []
    for k, (a, b) in enumerate(keep):
        nxt = keep[k + 1][0] if k + 1 < len(keep) else None
        tail = min(max_pause, max(0.0, (nxt - b))) if nxt is not None else 0.3
        graph.append(f"[0:a]atrim=start={a:.3f}:end={b + tail:.3f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.015,afade=t=out:st={max(0.0, b + tail - a - 0.015):.3f}:d=0.015[p{k}]")
        pieces.append(f"[p{k}]")
    _ff("-i", str(polished), "-filter_complex", ";".join(graph) + ";" + "".join(pieces)
        + f"concat=n={len(pieces)}:v=0:a=1[a]", "-map", "[a]", "-c:a", "pcm_s16le", str(dest))
    polished.unlink(missing_ok=True)

    def ts(x: float) -> str:
        return f"{int(x // 60)}:{x % 60:04.1f}"
    cut = [f"- {ts(parts[i][0].start)} retake «{' '.join(w.word.strip() for w in parts[i])[:120]}»" for i in sorted(drop)]
    cut += [f"- {ts(a)} repeated «{p}» ({b - a:.1f} s)" for a, b, p in sorted(stumbles)]
    cut += [f"- {ts(a)}–{ts(b)} cut as given in voice.yaml" for a, b in spans]
    before = words[-1].end - words[0].start if words else 0
    report = (f"## Own-voice recording\n\nCleaned: voice polish (no denoise) and gentle compression; pauses over "
              f"{max_pause:.1f} s shortened; {len(drop)} retake(s), {len(stumbles)} repeat(s) and {len(spans)} "
              f"given span(s) cut. Speech span {before / 60:.1f} min → the cleaned read.\n"
              + ("\nCut:\n" + "\n".join(cut) + "\n" if cut else "")
              + ("\n⚠️ Listed in `cut_repeats` but not heard twice — find it in the transcript below and add a "
                 "`cut:` span:\n" + "\n".join(f"- «{m}»" for m in missed) + "\n" if missed else "")
              + "\n<details><summary>Timed transcript of the recording (before cuts)</summary>\n\n"
              + "\n".join(f"- {ts(p[0].start)} {' '.join(w.word.strip() for w in p)}" for p in parts)
              + "\n\n</details>\n")
    log.info("Own voice: %d stretches, %d retakes, %d repeats, %d spans cut", len(parts), len(drop), len(stumbles), len(spans))
    return dest, report
