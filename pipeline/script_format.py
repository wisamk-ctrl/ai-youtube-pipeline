"""
Parsing for the marked-up script format shared by Phase 2 (length checks) and
Phase 3 (TTS text + editor cue sheet).

A script is plain text where anything inside [square brackets] is a production
marker and everything else is spoken. See prompts.MARKER_SPEC for the vocabulary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MARKER_RE = re.compile(r"\[(?P<body>[^\[\]]+)\]")
PAUSE_RE = re.compile(r"^pause(?:\s+(?P<secs>\d+(?:\.\d+)?)\s*s)?$", re.IGNORECASE)

# Arabic + Latin sentence terminators. The Arabic question mark (؟) and full
# stop variants matter: splitting only on "." would produce huge TTS chunks.
SENTENCE_END_RE = re.compile(r"(?<=[\.\!\?؟۔…])\s+")


def spoken_text(script: str) -> str:
    """The script with every marker removed — exactly what the presenter says."""
    text = MARKER_RE.sub(" ", script)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()


def count_spoken_words(script: str) -> int:
    return len(spoken_text(script).split())


@dataclass
class Cue:
    kind: str           # "section" | "broll" | "onscreen" | "pause" | "other"
    text: str
    at_word: int        # spoken-word offset where the cue fires
    at_seconds: float   # estimated timestamp, from words-per-minute


def extract_cues(script: str, words_per_minute: int) -> list[Cue]:
    """Build an editor's cue sheet: every non-spoken marker with an estimated timestamp.

    The estimate (word offset ÷ wpm) drifts by a few seconds over 8 minutes.
    It's meant to get the editor to the right spot quickly; final placement
    is done against the rendered video.
    """
    cues: list[Cue] = []
    words_so_far = 0
    pos = 0
    for m in MARKER_RE.finditer(script):
        words_so_far += len(script[pos : m.start()].split())
        pos = m.end()
        body = m.group("body").strip()
        head, _, rest = body.partition(":")
        key = head.strip().lower()
        if key == "section":
            kind = "section"
        elif key.startswith("show b-roll") or key == "b-roll":
            kind = "broll"
        elif key.startswith("on-screen"):
            kind = "onscreen"
        elif PAUSE_RE.match(body):
            kind = "pause"
        else:
            kind = "other"
        cues.append(
            Cue(kind=kind, text=(rest or body).strip(), at_word=words_so_far,
                at_seconds=round(words_so_far / words_per_minute * 60, 1))
        )
    return cues


# ---- Voice text: what the presenter's voice reads, as opposed to what subtitles show ----
# The W45 inspect report (2026-11-07) heard three faults the written script invites:
# a name written in both scripts («أوبن إيه آي OpenAI») is said twice, an English gloss in
# brackets («(AI agents)») is read aloud, and vowel marks make the voice misread
# («بُعد» → «بوعد»). speakable() fixes all three, plus a pronunciation map.

_AR = "\u0600-\u06FF"
_LATIN_RUN = re.compile(rf"(?P<ar>[{_AR}]+(?:\s+[{_AR}]+){{0,3}})\s+(?P<lat>[A-Za-z][A-Za-z0-9\-]*(?:\s+[A-Za-z][A-Za-z0-9\-]*){{0,3}})(?![A-Za-z0-9])")
_GLOSS = re.compile(rf"\s*\((?=[^()]*[A-Za-z])[^(){_AR}]*\)")
_HARAKAT = re.compile("[\u064B-\u0650\u0652\u0670]")     # every mark except shadda (U+0651)
_AR_CLASS = {**dict.fromkeys("بپ", "b"), **dict.fromkeys("تطث", "t"), **dict.fromkeys("دضذ", "d"),
             **dict.fromkeys("سص", "s"), **dict.fromkeys("كق", "k"), **dict.fromkeys("جغگ", "g"),
             **dict.fromkeys("فڤ", "f"), **dict.fromkeys("هح", "h"), "ش": "S", "ز": "z", "ر": "r",
             "ل": "l", "م": "m", "ن": "n", "خ": "k"}
_LAT_DIGRAPH = [("th", "t"), ("sh", "S"), ("ch", "S"), ("ph", "f"), ("ck", "k"), ("x", "ks")]
_LAT_CLASS = {"b": "b", "p": "b", "t": "t", "d": "d", "s": "s", "k": "k", "q": "k", "g": "g", "j": "g",
              "f": "f", "v": "f", "h": "h", "z": "z", "r": "r", "l": "l", "m": "m", "n": "n", "S": "S"}
_AR_PREFIXES = ("وال", "بال", "لل", "ال", "و", "ب", "ل", "ف")


def _ar_skeleton(word: str) -> str:
    return "".join(_AR_CLASS.get(ch, "") for ch in word)


def _lat_skeleton(word: str) -> str:
    w = word.lower()
    w = re.sub(r"c(?=[eiy])", "s", w).replace("c", "k")
    for a, b in _LAT_DIGRAPH:
        w = w.replace(a, b)
    out = "".join(_LAT_CLASS.get(ch, "") for ch in w)
    return re.sub(r"(.)\1+", r"\1", out)


def _same_name(arabic: list[str], latin: str) -> bool:
    """Is `latin` the English spelling of the Arabic words just before it? Compared on consonants."""
    return _same_name_words(arabic, latin) > 0


def _same_name_words(arabic: list[str], latin: str) -> int:
    """How many of the trailing Arabic words `latin` spells (0 when it is not the same name)."""
    from difflib import SequenceMatcher
    lat = _lat_skeleton(latin)
    if len(lat) < 2:
        return 0
    best, best_n = 0.0, 0
    for n in range(1, len(arabic) + 1):      # the closest-spelled tail wins; ties keep fewer words
        words = arabic[-n:]
        first = words[0]
        for pre in ("",) + _AR_PREFIXES:
            if pre and not (first.startswith(pre) and len(first) > len(pre) + 1):
                continue
            ar = _ar_skeleton(first[len(pre):] + "".join(words[1:]))
            ar = re.sub(r"(.)\1+", r"\1", ar)
            ratio = SequenceMatcher(None, ar, lat).ratio() if ar else 0.0
            if ratio >= 0.75 and ratio > best + 1e-9:
                best, best_n = ratio, n
    return best_n


def _pronunciation(path=None) -> dict[str, str]:
    from pathlib import Path
    p = Path(path) if path else Path(__file__).resolve().parent.parent / "config" / "pronunciation.yaml"
    if not p.exists():
        return {}
    import yaml
    return {str(k): str(v) for k, v in (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).items()}


def speakable(text: str, pronunciation: dict[str, str] | None = None) -> str:
    """Spoken text → what the voice should read: names once, no English glosses, no vowel marks."""
    text = _GLOSS.sub("", text)

    def _dedupe(m: re.Match) -> str:
        return m.group("ar") if _same_name(m.group("ar").split(), m.group("lat")) else m.group(0)
    text = _LATIN_RUN.sub(_dedupe, text)
    pron = _pronunciation() if pronunciation is None else pronunciation
    for key in sorted(pron, key=len, reverse=True):
        text = re.sub(rf"(?<![A-Za-z0-9]){re.escape(key)}(?![A-Za-z0-9])", pron[key], text)
    text = _HARAKAT.sub("", text)
    return re.sub(r"[ \t]+", " ", text)


def to_tts_text(script: str, pause_style: str = "ssml", default_pause: float = 0.8,
                voice_fixes: bool = True) -> str:
    """Convert the script into what the speech engine should receive.

    * [Pause] / [Pause 2s] → an SSML break tag (or an ellipsis for engines without SSML)
    * every other marker   → removed
    """

    def _replace(m: re.Match[str]) -> str:
        pm = PAUSE_RE.match(m.group("body").strip())
        if not pm:
            return " "
        secs = float(pm.group("secs") or default_pause)
        secs = min(secs, 3.0)  # ElevenLabs caps a break at 3s; longer ones are ignored
        return f' <break time="{secs:.1f}s"/> ' if pause_style == "ssml" else " ... "

    text = MARKER_RE.sub(_replace, script)
    if voice_fixes:
        text = speakable(text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\s*\n\s*", "\n", text).strip()


def chunk_text(text: str, max_chars: int) -> list[str]:
    """Split TTS text into chunks of ≤ max_chars on sentence boundaries.

    Avatar/TTS APIs cap the text per request (or per scene). Cutting
    mid-sentence produces audible prosody breaks, so we pack whole sentences
    greedily and only hard-split a single sentence that is itself too long.
    """
    sentences = [s.strip() for s in SENTENCE_END_RE.split(text.replace("\n", " ")) if s.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        while len(sentence) > max_chars:  # pathological run-on sentence
            cut = sentence.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if current and len(current) + 1 + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


# ── Shot markers (config/visual_standard.md) ─────────────────────────────────
SHOT_KINDS = ("source", "number", "title", "stock")


@dataclass
class ShotMark:
    mode: str           # "face" | "visual" | "corner"
    kind: str           # "" for face, else one of SHOT_KINDS
    payload: str        # item id, "figure | label", phrase, or stock search terms
    at_word: int        # spoken-word offset where the shot starts


def parse_shot(body: str) -> tuple[str, str, str] | None:
    """`Face` / `Visual: <kind> <payload>` / `Corner: <kind> <payload>` → (mode, kind, payload)."""
    body = body.strip()
    if body.lower() == "face":
        return ("face", "", "")
    head, sep, rest = body.partition(":")
    mode = head.strip().lower()
    if not sep or mode not in ("visual", "corner"):
        return None
    kind, _, payload = rest.strip().partition(" ")
    kind = kind.strip().lower()
    if kind not in SHOT_KINDS or not payload.strip():
        return None
    return (mode, kind, payload.strip())


def extract_shots(script: str) -> list[ShotMark]:
    """Every shot marker, in order, with the spoken-word offset where it fires."""
    shots: list[ShotMark] = []
    words, pos = 0, 0
    for m in MARKER_RE.finditer(script):
        words += len(MARKER_RE.sub(" ", script[pos:m.start()]).split())
        pos = m.end()
        parsed = parse_shot(m.group("body"))
        if parsed:
            shots.append(ShotMark(*parsed, at_word=words))
    return shots


def has_shots(script: str) -> bool:
    return bool(extract_shots(script))


def strip_shots(script: str) -> str:
    """The script without shot markers (for re-directing); every other marker and word is kept."""
    keep = [line for line in script.splitlines()
            if not ((m := MARKER_RE.fullmatch(line.strip())) and parse_shot(m.group("body")))]
    return "\n".join(keep)
