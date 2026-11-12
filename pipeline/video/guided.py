"""
The founder's recordings, edited by following the approved script (2026-11-12).

W45 took a day of hand-listed cuts because the edit only knew the recording. The script says what
was meant, so the recording is walked against it word by word:

- a jump back in the script is a retake: the later saying wins, the earlier one is cut;
- words heard between two neighbouring script words that repeat the words around them are a
  stumble («وشركات وشركات», «… أو AgentCore Bedrock») and are cut;
- a further file (`pickups:` in voice.yaml) is walked the same way, so a sentence re-read later
  replaces the one in the main take, wherever it falls;
- script passages with no match are listed for the founder to check by ear (a misread or a skip).

The output follows script order. `cut:` spans still force a cut and `keep:` spans forbid one, both
in the first file's recording time. Pure functions here; the audio work is in `render()`.
"""

from __future__ import annotations

import logging
import wave
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

from pipeline.post.subtitles import Word, norm_word

log = logging.getLogger(__name__)

AHEAD = 12          # script words searched ahead of the expected one
SENTENCE_END = (".", "؟", "?", "!", "…", ":")


_AR = {"ب": "b", "ت": "t", "ث": "t", "ج": "j", "ح": "h", "خ": "k", "د": "d", "ذ": "d", "ر": "r", "ز": "s",
       "س": "s", "ش": "s", "ص": "s", "ض": "d", "ط": "t", "ظ": "s", "غ": "j", "ف": "f", "ق": "k", "ك": "k",
       "ل": "l", "م": "m", "ن": "n", "ه": "h", "ة": "", "پ": "b", "ڤ": "f", "چ": "j"}
_LAT = {"b": "b", "c": "k", "d": "d", "f": "f", "g": "j", "h": "h", "j": "j", "k": "k", "l": "l", "m": "m",
        "n": "n", "p": "b", "q": "k", "r": "r", "s": "s", "t": "t", "v": "f", "x": "ks", "z": "s"}


def skeleton(word: str) -> str:
    """Consonants only, in one alphabet: «اوكتا» and «okta» both give «kt», «بدروك» and «bedrock»
    «bdrk». The recogniser writes an English name in either script, run to run."""
    out = []
    for i, ch in enumerate(word):
        if ch == "c" and word[i + 1:i + 2] in ("e", "i", "y"):
            c = "s"
        else:
            c = _AR.get(ch) or _LAT.get(ch, "")
        for x in c:
            if not out or out[-1] != x:
                out.append(x)
    return "".join(out)


def _latin(w: str) -> bool:
    return any("a" <= c <= "z" for c in w)


def _ratio(a: str, b: str) -> float:
    if a == b:
        return 1.0
    r = SequenceMatcher(None, a, b).ratio()
    if a and b and _latin(a) != _latin(b):     # one in Latin letters, one in Arabic: compare the consonants
        x, y = skeleton(a), skeleton(b)
        if min(len(x), len(y)) >= 2:
            r = max(r, 1.0 if x == y else SequenceMatcher(None, x, y).ratio() * (0.9 if min(len(x), len(y)) >= 3 else 0.0))
    return r


def _sim(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return a == b or (min(len(a), len(b)) >= 3 and _ratio(a, b) >= 0.75)


def follow(script: list[str], heard: list[str], file_starts: frozenset[int] | set[int] = frozenset()
           ) -> tuple[list[int | None], list[int], dict[int, int]]:
    """For every heard word, the script word it says (or None) and the take it belongs to; `more[k]`
    is a second script word the same heard word covers («OktaCross» for «Okta Cross»).

    `script` and `heard` are normalised words. A new take starts at every file start and every time
    the speaker leaves the script's order (a retake, or a jump far from the expected word)."""
    n, m = len(script), len(heard)
    at: list[int | None] = [None] * m
    take = [0] * m
    more: dict[int, int] = {}
    live = [k for k in range(m) if heard[k]]
    after = {a: b for a, b in zip(live, live[1:])}

    def chain(k: int | None, j: int, limit: int = 6) -> int:
        """How many heard words from k say the script from j, in a row."""
        c = 0
        while k is not None and j < n and c < limit and _sim(heard[k], script[j]):
            c, k, j = c + 1, after.get(k), j + 1
        return c

    def jump(k: int, lo: int, hi: int, need: int, pos: int) -> int | None:
        k1 = after.get(k)
        avail = 1 + (k1 is not None) + (k1 is not None and after.get(k1) is not None)
        best, score = None, (0, 0.0)
        for j in range(max(0, lo), min(n, hi)):
            if not _sim(heard[k], script[j]):
                continue
            c = chain(k, j)
            if c < min(need, avail, n - j) or c < 2:
                continue
            sc = (c, -abs(j - pos) - (0.5 if j > pos else 0))     # longest match, then nearest, back before ahead
            if best is None or sc > score:
                best, score = j, sc
        return best

    pos, cur, lost, glued = 0, -1, True, -1
    for k in range(m):
        if k in file_starts or k == 0:
            cur, lost = cur + 1, True
        take[k] = cur
        h = heard[k]
        if not h:
            continue
        if k == glued:                 # the second half of «Agent Core» → «AgentCore»
            at[k] = at[k - 1] if at[k - 1] is not None else pos - 1
            continue
        j, k1 = None, after.get(k)
        if lost:
            j = jump(k, 0, n, 3, pos)
        else:
            if pos < n and _sim(h, script[pos]):
                j = pos
            elif (pos < n and k1 == k + 1 and not _sim(heard[k1], script[pos])
                  and _ratio(h + heard[k1], script[pos]) >= 0.8):
                j, glued = pos, k1
            elif pos + 1 < n and len(h) >= 6 and _ratio(h, script[pos] + script[pos + 1]) >= 0.8:
                j, more[k] = pos + 1, pos
            else:
                for c in range(pos + 1, min(n, pos + AHEAD)):
                    if _sim(h, script[c]) and (chain(k, c) >= 2 or (len(h) >= 5 and h == script[c])):
                        j = c
                        break
            if j is None:
                j = jump(k, pos - 40, pos, 3, pos)           # a retake
                if j is None:
                    j = next((c for c in range(pos + 1, min(n, pos + 3)) if _ratio(h, script[c]) >= 0.85
                              and len(h) >= 3), None)
                    if j is None:
                        j = jump(k, 0, n, 4, pos)           # far from the expected word: a strong match only
                    if j is not None and not pos < j < pos + AHEAD:
                        cur += 1
                        take[k] = cur
                else:
                    cur += 1
                    take[k] = cur
        if j is not None:
            at[k], pos, lost = j, j + 1, False
    for k, j in list(more.items()):
        if at[k] is None:
            del more[k]
    return at, take, more


@dataclass
class Plan:
    keep: list[bool]                               # per heard word
    pieces: list[tuple[int, int]]                  # heard index ranges (inclusive), in output order
    dropped: list[tuple[int, int, str]] = field(default_factory=list)   # (first, last, why)
    unheard: list[tuple[int, int]] = field(default_factory=list)        # script index ranges with no match
    owner: dict[int, int] = field(default_factory=dict)                 # script word → kept heard word


def choose(script: list[str], heard: list[str], at: list[int | None], take: list[int],
           gaps: list[float], banned: set[int] = frozenset(), forced: set[int] = frozenset(),
           more: dict[int, int] | None = None) -> Plan:
    """Which heard words stay. `gaps[k]` is the silence before word k (s)."""
    m, n, more = len(heard), len(script), more or {}
    owner: dict[int, int] = {}
    for k in range(m):
        if at[k] is not None and k not in banned:
            for j in (at[k], more.get(k, at[k])):
                owner[j] = max(owner.get(j, -1), take[k])
    keep = [at[k] is not None and k not in banned and owner[at[k]] == take[k] for k in range(m)]
    why = ["retake" if at[k] is not None else "" for k in range(m)]
    k = 0
    while k < m:
        if at[k] is not None or k in banned:
            k += 1
            continue
        e = k
        while e + 1 < m and at[e + 1] is None and e + 1 not in banned and take[e + 1] == take[k]:
            e += 1
        a = k - 1 if k > 0 and take[k - 1] == take[k] and at[k - 1] is not None else None
        b = e + 1 if e + 1 < m and take[e + 1] == take[k] and at[e + 1] is not None else None
        run = [x for x in range(k, e + 1) if heard[x]]
        stay = {x: False for x in range(k, e + 1)}
        if a is not None and b is not None:
            ja, jb = at[a], at[b]
            text = "".join(heard[x] for x in run)
            glued = (_ratio(text + heard[b], script[jb]) > max(0.8, _ratio(heard[b], script[jb]))
                     or _ratio(heard[a] + text, script[ja]) > max(0.8, _ratio(heard[a], script[ja])))
            # Words that are (loosely) the script's own words between the two anchors stay.
            mine, ptr = set(), ja + 1
            for x in run:
                hit = next((j for j in range(ptr, jb) if _ratio(heard[x], script[j]) >= 0.6), None)
                if hit is not None:
                    mine.add(x)
                    ptr = hit + 1
            # A stumble repeats words that are also said properly nearby. A word whose script word
            # nobody said is not a repeat: the speaker moved it («بنظام Vera» for «Vera بنظام»), keep it.
            said = [j for j in range(max(0, ja - 6), min(n, jb + 7)) if j in owner]
            near = [script[j] for j in said]
            pairs = [script[j] + script[j + 1] for j in said if j + 1 in owner and j + 1 < n]

            def echo(i: int) -> bool:
                x = run[i]
                if x in mine:
                    return False
                h = heard[x]
                if len(h) < 3:              # «أو», «با», spelled letters: never a repeat by themselves
                    return False
                if any(_sim(h, s) for s in near) or (len(h) >= 6 and any(_ratio(h, s) >= 0.8 for s in pairs)):
                    return True
                sides = [run[i + d] for d in (-1, 1) if 0 <= i + d < len(run) and run[i + d] not in mine]
                return any(_ratio(*((heard[y] + h, s) if y < x else (h + heard[y], s))) >= 0.8
                           for y in sides for s in near if len(s) >= 6)
            stumble = set() if glued else {run[i] for i in range(len(run)) if echo(i)}
            for i in range(len(run) - 2, -1, -1):          # «أو» before the repeated words goes with them
                if run[i] not in stumble and run[i] not in mine and len(heard[run[i]]) <= 2 and run[i + 1] in stumble:
                    stumble.add(run[i])
            rest = keep[b] or (keep[a] and jb > ja + 1 and not any(j in owner for j in range(ja + 1, jb)))
            for x in stay:
                stay[x] = rest and x not in stumble
        elif b is not None:          # before a take's first matched word
            stay = dict.fromkeys(stay, keep[b] and gaps[b] < 0.6)
        elif a is not None:          # a take's tail: a stumble if the next take goes back over it
            nxt = next((at[x] for x in range(e + 1, m) if at[x] is not None), None)
            restart = e + 1 < m and nxt is not None and nxt <= at[a] and gaps[e + 1] < 30
            stay = dict.fromkeys(stay, keep[a] and not restart)
        for x in range(k, e + 1):
            keep[x] = stay[x] or (x in forced)
            why[x] = "extra"
        k = e + 1
    for k in forced:
        if 0 <= k < m and k not in banned:
            keep[k] = True
    # Pieces: runs of kept words that are neighbours in the recording and in the script.
    pieces: list[tuple[int, int, float]] = []
    start, last_j = None, None
    for k in range(m + 1):
        ok = k < m and keep[k]
        j = at[k] if ok else None
        split = ok and start is not None and (take[k] != take[k - 1] or (
            j is not None and last_j is not None and any(owner.get(x, take[k]) != take[k] for x in range(last_j + 1, j))))
        if (not ok or split) and start is not None:
            pieces.append((start, k - 1, _key(at, start, k - 1)))
            start, last_j = None, None
        if ok:
            if start is None:
                start = k
            if j is not None:
                last_j = j
    pieces.sort(key=lambda p: (p[2], p[0]))
    dropped, k = [], 0
    while k < m:
        if keep[k] or not heard[k]:
            k += 1
            continue
        e, tag = k, "given" if k in banned else why[k]
        while e + 1 < m and not keep[e + 1] and (("given" if e + 1 in banned else why[e + 1]) == tag or not heard[e + 1]):
            e += 1
        dropped.append((k, e, tag))
        k = e + 1
    said = {}
    for k in range(m):
        if keep[k] and at[k] is not None:
            said[at[k]] = k
            said[more.get(k, at[k])] = k
    unheard, j = [], 0
    while j < n:
        if j in said:
            j += 1
            continue
        e = j
        while e + 1 < n and e + 1 not in said:
            e += 1
        if e - j >= 2:
            unheard.append((j, e))
        j = e + 1
    return Plan(keep, [(a, b) for a, b, _ in pieces], dropped, unheard, said)


def _key(at: list[int | None], a: int, b: int) -> float:
    js = [at[k] for k in range(a, b + 1) if at[k] is not None]
    return js[0] if js else float("inf")


@dataclass
class Atom:
    file: int
    a: float
    b: float            # audio taken from a to b (b includes the room tone of the pause)
    pad: float = 0.0    # silence added after it
    first: int = 0      # heard words first..last sit in this atom
    last: int = 0


def atoms(words: list[Word], files: list[int], plan: Plan, ends: list[bool], at: list[int | None],
          lengths: list[float], max_pause: float = 0.5, pad: float = 0.08) -> list[Atom]:
    """Audio spans for the plan's pieces, each internal pause capped at `max_pause`. `ends[j]` says
    script word j ends a sentence; a splice gets a sentence pause there and a short one elsewhere."""
    out: list[Atom] = []
    m = len(words)
    for pi, (p0, p1) in enumerate(plan.pieces):
        k = p0
        while k <= p1:
            e = k
            while e < p1 and words[e + 1].start - words[e].end <= max_pause:
                e += 1
            f = files[k]
            prev_end = words[k - 1].end if k > 0 and files[k - 1] == f else 0.0
            nxt_start = words[e + 1].start if e + 1 < m and files[e + 1] == f else lengths[f]
            a = max(words[k].start - pad, min(prev_end, words[k].start), 0.0)
            b = max(min(words[e].end + pad, nxt_start), a + 0.02)
            room = max(0.0, nxt_start - b)
            if e < p1:                       # a pause inside the piece
                want = max_pause
            elif pi == len(plan.pieces) - 1:
                want = 0.3
            else:                            # a splice
                js = [at[x] for x in range(k, e + 1) if at[x] is not None]
                want = 0.45 if js and ends[js[-1]] else 0.12
            tone = min(want, room)
            out.append(Atom(f, a, b + tone, want - tone, k, e))
            k = e + 1
    return out


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        rate, ch = w.getframerate(), w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, ch)
    return data, rate


def render(wavs: list[Path], spans: list[Atom], dest: Path, words: list[Word], fade: float = 0.015
           ) -> list[Word]:
    """Join the atoms into dest (16-bit wav) with short fades; returns the kept words at their new times."""
    loaded = [read_wav(p) for p in wavs]
    rate = loaded[0][1]
    parts, moved, t = [], [], 0.0
    for s in spans:
        data = loaded[s.file][0]
        x = data[int(s.a * rate):int(s.b * rate)].astype(np.float32)
        n = min(int(fade * rate), len(x) // 2)
        if n:
            ramp = np.linspace(0.0, 1.0, n, dtype=np.float32)[:, None]
            x[:n] *= ramp
            x[-n:] *= ramp[::-1]
        parts.append(x.astype("<i2"))
        if s.pad > 0:
            parts.append(np.zeros((int(s.pad * rate), data.shape[1]), dtype="<i2"))
        for k in range(s.first, s.last + 1):
            w = words[k]
            moved.append(Word(round(t + w.start - s.a, 3), round(t + w.end - s.a, 3), w.word))
        t += len(x) / rate + (int(s.pad * rate) / rate if s.pad > 0 else 0.0)
    joined = np.concatenate(parts) if parts else np.zeros((0, 2), dtype="<i2")
    with wave.open(str(dest), "wb") as w:
        w.setnchannels(joined.shape[1])
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(joined.tobytes())
    return moved


def reading_text(md: str) -> str:
    """The words of a reading script (reviewed/<week>/read_script.md): everything under its `##`
    headings; the title, the word count and the headings themselves are not read aloud."""
    lines, seen = [], False
    for line in md.splitlines():
        if line.startswith("#"):
            seen = seen or line.startswith("## ")
            continue
        if seen:
            lines.append(line)
    return "\n".join(lines).strip()


def script_tokens(spoken: str) -> tuple[list[str], list[str]]:
    """(raw words, normalised words) of the spoken script, words with no letters dropped."""
    from pipeline.script_format import spoken_words, unbraced
    raw = [w for w in spoken_words(unbraced(spoken)) if norm_word(w)]
    return raw, [norm_word(w) for w in raw]


def guide(spoken: str, words: list[Word], files: list[int], lengths: list[float],
          cut: list[tuple[float, float]] | None = None, keep: list[tuple[float, float]] | None = None,
          max_pause: float = 0.5) -> tuple[Plan, list[Atom], list[int | None], list[str]]:
    """The whole decision for a set of transcribed files. `files[k]` is the file of word k."""
    raw, script = script_tokens(spoken)
    heard = [norm_word(w.word) for w in words]
    starts = {k for k in range(len(words)) if k == 0 or files[k] != files[k - 1]}
    at, take, more = follow(script, heard, starts)

    def inside(k: int, spans) -> bool:
        return files[k] == 0 and any(a <= (words[k].start + words[k].end) / 2 < b for a, b in spans or [])
    banned = {k for k in range(len(words)) if inside(k, cut)}
    forced = {k for k in range(len(words)) if inside(k, keep)}
    gaps = [words[k].start - words[k - 1].end if k and files[k] == files[k - 1] else 99.0 for k in range(len(words))]
    plan = choose(script, heard, at, take, gaps, banned, forced, more)
    ends = [r.rstrip("»\"')”").endswith(SENTENCE_END) for r in raw]
    return plan, atoms(words, files, plan, ends, at, lengths, max_pause), at, raw


def report(plan: Plan, words: list[Word], files: list[int], at: list[int | None], raw: list[str],
           names: list[str], before: float, after: float) -> str:
    def ts(x: float) -> str:
        return f"{int(x // 60)}:{x % 60:04.1f}"

    def where(k: int) -> str:
        return (f"{names[files[k]]} " if len(names) > 1 else "") + ts(words[k].start)

    def said(a: int, b: int) -> str:
        return " ".join(w.word.strip() for w in words[a:b + 1])[:160]
    label = {"retake": "said again later, this one cut", "extra": "stumble cut", "given": "cut as given in voice.yaml"}
    lines = [f"## Own-voice recording (edited by the script)\n",
             f"{len(names)} file(s), {before / 60:.1f} min of recording → {after / 60:.1f} min. "
             f"{sum(1 for d in plan.dropped if d[2] == 'retake')} retake(s), "
             f"{sum(1 for d in plan.dropped if d[2] == 'extra')} stumble(s) and "
             f"{sum(1 for d in plan.dropped if d[2] == 'given')} given span(s) cut. "
             "Listen to the voice check before the video is made.\n"]
    if plan.dropped:
        lines.append("### Cut\n")
        lines += [f"- {where(a)} «{said(a, b)}» — {label[tag]}" for a, b, tag in plan.dropped]
        lines.append("\nA wrong cut: add `keep: [\"m:ss-m:ss\"]` to voice.yaml. A missed one: add it to `cut:`.\n")
    moved = [(a, b) for a, b in plan.pieces if files[a] != 0]
    if moved:
        lines.append("### Pickups used\n")
        lines += [f"- {where(a)} «{said(a, b)}»" for a, b in moved]
        lines.append("")
    if plan.unheard:
        owner = plan.owner
        lines.append("### Check by ear: script passages the recogniser did not find\n")
        lines.append("Often only the recogniser's spelling (names, numbers). A real misread: re-read the "
                     "sentence into a new file and list it under `pickups:`.\n")
        for a, b in plan.unheard:
            lo = max((k for j, k in owner.items() if j < a), default=None)
            hi = min((k for j, k in owner.items() if j > b), default=None)
            got = said(lo + 1, hi - 1) if lo is not None and hi is not None and hi - lo > 1 else ""
            t = where(lo) if lo is not None else "start"
            lines.append(f"- after {t}: script «{' '.join(raw[a:b + 1])[:160]}» · heard «{got}»")
        lines.append("")
    return "\n".join(lines) + "\n"
