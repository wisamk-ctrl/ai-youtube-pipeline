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


def to_tts_text(script: str, pause_style: str = "ssml", default_pause: float = 0.8) -> str:
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
