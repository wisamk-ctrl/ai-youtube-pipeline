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


# «أوبن إيه آي{OpenAI}»: the Latin spelling of the name just before it. Never spoken; subtitles
# show it as «أوبن إيه آي (OpenAI)». A word with its braces is one word, spaces inside or not.
_BRACED = re.compile(r"\{[^{}]*\}")
_WORD_RE = re.compile(r"[^\s{}]*\{[^{}]*\}[^\s{}]*|\S+")


def spoken_words(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def count_spoken_words(script: str) -> int:
    return len(spoken_words(spoken_text(script)))


def unbraced(text: str) -> str:
    return _BRACED.sub("", text)


def caption_text(text: str) -> str:
    """Braced Latin names as subtitles show them: «أوبن إيه آي{OpenAI}» → «أوبن إيه آي (OpenAI)»."""
    return _BRACED.sub(lambda m: f" ({m.group(0)[1:-1].strip()})", text)


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
        words_so_far += len(spoken_words(script[pos : m.start()]))
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
_HAS_AR = re.compile(f"[{_AR}]")
_LATIN_RUN = re.compile(rf"(?P<ar>[{_AR}]+(?:\s+[{_AR}]+){{0,3}})\s+(?P<lat>[A-Za-z][A-Za-z0-9\-]*(?:\s+[A-Za-z][A-Za-z0-9\-]*){{0,3}})(?![A-Za-z0-9])")
_GLOSS = re.compile(rf"\s*\((?=[^()]*[A-Za-z])[^(){_AR}]*\)")
_NAME_IN_GLOSS = re.compile(r"[A-Z][a-z]|\d")       # «(Claude Opus 4.5)» is a name, «(AI agents)» a gloss


def _drop_gloss(m: re.Match) -> str:
    inner = m.group(0).strip()[1:-1]
    return " " + inner if _NAME_IN_GLOSS.search(inner) else ""
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
    for a, b in _LAT_DIGRAPH:      # before c→k, or «ChatGPT» turns into k-h-…
        w = w.replace(a, b)
    w = re.sub(r"c(?=[eiy])", "s", w).replace("c", "k")
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
    """Spoken text → what the voice should read: names once, no English glosses, no vowel marks.

    Braced Latin («أوبن إيه آي{OpenAI}») is dropped outright; the consonant match below is only
    for older scripts that wrote the two spellings side by side.

    Text with no Arabic letters (the English version, phase translate) passes through as written:
    its brackets are not glosses, and the Arabic respellings in config/pronunciation.yaml are not
    for an English voice."""
    if not _HAS_AR.search(text):
        return re.sub(r"[ \t]+", " ", text)
    text = _GLOSS.sub(_drop_gloss, unbraced(text))
    pron = _pronunciation() if pronunciation is None else pronunciation

    def _dedupe(m: re.Match) -> str:
        ar, lat = m.group("ar"), m.group("lat")
        said = pron.get(lat.strip())
        if said and ar.replace("و", "").endswith(said.replace("و", "")):
            return ar                        # «جي فورتي تو G42»: the respelling is already there
        return ar if _same_name(ar.split(), lat) else m.group(0)
    text = _LATIN_RUN.sub(_dedupe, text)
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


# ── Voice lint: what the voice will read, checked against style guide §2–§6 ──────────────────
# The critic reads the written script; this reads speakable() output, which is what the clone
# says. Findings go to output/<week>/voice_lint.md and into the reviewer's and critic's notes.

PAUSE_MARK = "⏸"
_SENT_SPLIT = re.compile(r"(?<=[.!?؟…])\s+|\n+")
_LAT_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+\-]*")
_VERSION = re.compile(r"(?<![\w.])[vV]?\d+(?:\.\d+){2,}(?!\w|\.\d)")
_WHY_IT_MATTERS = re.compile(r"ليش\s+(?:(?:هاد|هاي|هالإشي|الإشي)\s+)?(?:بيهم|مهم)")
_PREP_PAUSE = re.compile(rf"(?<![{_AR}])[لبك]ـ?\s*{PAUSE_MARK}")
_GREETING = re.compile(r"أهلا\s+فيكم|أهلا\s+وسهلا")
_NUMBER_WORDS = {
    "اتنين", "تنين", "تلات", "تلاته", "تلاتين", "اربع", "اربعه", "اربعين", "خمس", "خمسه",
    "خمسين", "ست", "سته", "ستين", "سبع", "سبعه", "سبعين", "تمان", "تمانيه", "تمانين", "تسع", "تسعه",
    "تسعين", "عشر", "عشره", "عشرين", "ميه", "مئه", "ميتين", "تلتميه", "اربعميه", "خمسميه",
    "ستميه", "سبعميه", "تمنميه", "تسعميه", "الف", "الفين", "الاف", "مليون",
    "مليونين", "ملايين", "مليار", "مليارين", "مليارات", "تريليون", "بالميه",
}
_NUMBER_JOINERS = {"فاصله", "و", "ونص", "وربع"}
HOOK_MAX_WORDS = 45
WHY_IT_MATTERS_MAX = 3
LATIN_PER_SENTENCE_MAX = 2

RULES = {
    "latin": "Latin word the voice reads: write it in Arabic letters with the Latin in braces on first mention («أوبن إيه آي{OpenAI}»); bare Latin only for the allowlist",
    "digits": "letters and digits in one token: add it to config/pronunciation.yaml, write it as spoken with the Latin in braces, or paraphrase",
    "version": "version string read aloud: say «آخر إصدار» and put the number in an [On-Screen Text] cue",
    "parentheses": "parentheses left in the voice text: no glosses or asides in brackets",
    "latin-stack": f"more than {LATIN_PER_SENTENCE_MAX} Latin words in one sentence: split it or say them in Arabic",
    "figures": "two figures in one breath: put a [Pause] between them or split the sentence",
    "preposition-pause": "pause between a one-letter preposition and its number: «لخمس سنين», not «لـ [Pause] خمس سنين»",
    "banned": "banned phrase",
    "why-it-matters": f"«ليش بيهمّنا» wording used more than {WHY_IT_MATTERS_MAX} times: vary the question",
    "hook-length": f"hook (before the greeting) over {HOOK_MAX_WORDS} words: one story, one number, one question",
}


@dataclass
class VoiceFinding:
    rule: str
    quote: str
    detail: str = ""


def _voice_config(path=None) -> dict:
    from pathlib import Path
    p = Path(path) if path else Path(__file__).resolve().parent.parent / "config" / "voice.yaml"
    if not p.exists():
        return {}
    import yaml
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _norm_ar(word: str) -> str:
    w = re.sub("[ً-ْٰـ]", "", word)
    return re.sub("[أإآ]", "ا", w).replace("ة", "ه").replace("ى", "ي")


def _is_number_word(word: str) -> bool:
    w = _norm_ar(re.sub(rf"[^{_AR}]", "", word))
    candidates = {w}
    if w[:1] in ("و", "ب", "ل"):
        candidates.add(w[1:])
    if w[:2] in ("وب", "ول"):
        candidates.add(w[2:])
    return bool(candidates & _NUMBER_WORDS)


def _figures(chunk: str) -> int:
    """Figures in a pause-free stretch: runs of number words or bare digits, not digits in a name."""
    n, in_run, prev_latin = 0, False, False
    for tok in chunk.split():
        bare = tok.strip("«»\"'،,.:؛;!?؟%")
        is_digits = bool(re.fullmatch(r"\d+(?:[.,]\d+)?%?", bare)) and not prev_latin
        is_num = is_digits or _is_number_word(tok)
        if in_run and _norm_ar(bare) in _NUMBER_JOINERS:
            continue
        if is_num and not in_run:
            n += 1
        in_run = is_num
        prev_latin = bool(re.search(r"[A-Za-z]", bare))
    return n


def _short(s: str, n: int = 90) -> str:
    s = s.replace(PAUSE_MARK, "...").strip()
    return s if len(s) <= n else s[:n].rstrip() + "…"


def voice_text(script: str, pronunciation: dict[str, str] | None = None) -> str:
    """speakable() of the spoken text, with every pause ([Pause], or «...» in a paste pack) kept as ⏸."""
    def _marker(m: re.Match) -> str:
        return f" {PAUSE_MARK} " if PAUSE_RE.match(m.group("body").strip()) else " "
    text = MARKER_RE.sub(_marker, script)
    text = text.replace("...", f" {PAUSE_MARK} ")
    return speakable(text, pronunciation)


def lint_voice(script: str, pronunciation: dict[str, str] | None = None,
               config: dict | None = None) -> list[VoiceFinding]:
    """Every place where what the voice reads breaks the voice rules (style guide §2–§6).
    The rules are Arabic rules: a script with no Arabic letters (the English version) has none."""
    if not _HAS_AR.search(MARKER_RE.sub(" ", script)):
        return []
    cfg = _voice_config() if config is None else config
    allow = {str(x) for x in cfg.get("latin_allowlist", [])}
    banned = {str(k): str(v or "") for k, v in (cfg.get("banned_phrases") or {}).items()}
    text = voice_text(script, pronunciation)
    sentences = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip(f" {PAUSE_MARK}")]
    out: list[VoiceFinding] = []
    latin: dict[str, int] = {}
    mixed: dict[str, int] = {}

    for sent in sentences:
        for m in _VERSION.finditer(sent):
            out.append(VoiceFinding("version", m.group(0), _short(sent)))
        no_versions = _VERSION.sub(" ", sent)
        words = [t.rstrip(".-") for t in _LAT_TOKEN.findall(no_versions)]
        words = [t for t in words if re.search(r"[A-Za-z]", t)]
        for t in words:
            if re.search(r"\d", t):
                mixed[t] = mixed.get(t, 0) + 1
            elif t not in allow:
                latin[t] = latin.get(t, 0) + 1
        if len([t for t in words if t not in allow]) > LATIN_PER_SENTENCE_MAX:
            out.append(VoiceFinding("latin-stack", _short(sent), ", ".join(words)))
        if "(" in sent or ")" in sent:
            out.append(VoiceFinding("parentheses", _short(sent)))
        if any(_figures(chunk) >= 2 for chunk in sent.split(PAUSE_MARK)):
            out.append(VoiceFinding("figures", _short(sent)))
        for m in _PREP_PAUSE.finditer(sent):
            out.append(VoiceFinding("preposition-pause", _short(sent[max(0, m.start() - 30):m.end() + 30])))

    for t, n in sorted(mixed.items(), key=lambda kv: -kv[1]):
        out.append(VoiceFinding("digits", t, f"{n}×"))
    for t, n in sorted(latin.items(), key=lambda kv: -kv[1]):
        out.append(VoiceFinding("latin", t, f"{n}×"))

    flat = _norm_ar(text.replace("ّ", ""))
    for phrase, instead in banned.items():
        prefix = phrase.endswith("ـ")
        key = _norm_ar(phrase.rstrip("ـ"))
        pat = rf"(?<![{_AR}]){re.escape(key)}" + ("" if prefix else rf"(?![{_AR}])")
        n = len(re.findall(pat, flat))
        if n:
            out.append(VoiceFinding("banned", phrase, f"{n}× → «{instead}»" if instead else f"{n}×"))

    why = _WHY_IT_MATTERS.findall(text.replace("ّ", ""))
    if len(why) > WHY_IT_MATTERS_MAX:
        out.append(VoiceFinding("why-it-matters", "ليش بيهمّنا", f"{len(why)}×"))

    g = _GREETING.search(text)
    if g:
        hook_words = [w for w in text[:g.start()].split() if w != PAUSE_MARK]
        if len(hook_words) > HOOK_MAX_WORDS:
            out.append(VoiceFinding("hook-length", _short(" ".join(hook_words[:12])), f"{len(hook_words)} words"))
    return out


def voice_lint_md(findings: list[VoiceFinding], title: str = "Voice lint") -> str:
    lines = [f"# {title}", "",
             f"**{len(findings)} findings** on the text the voice reads (`speakable()` output). "
             "Rules: `config/style_guide.md` §2–§6, `config/voice.yaml`.", ""]
    for rule, why in RULES.items():
        hits = [f for f in findings if f.rule == rule]
        if not hits:
            continue
        lines += [f"## {rule} ({len(hits)})", f"_{why}_", ""]
        lines += [f"- «{f.quote}»" + (f" — {f.detail}" if f.detail else "") for f in hits]
        lines.append("")
    return "\n".join(lines)


def voice_lint_notes(findings: list[VoiceFinding], limit: int = 40) -> str:
    """The findings as instructions for the reviewer, or as evidence for the critic. Empty if clean."""
    if not findings:
        return ""
    lines = [f"A deterministic lint of the text the voice will read found {len(findings)} voice-rule problems "
             "(style guide §2–§6). Fix each one in the script:"]
    for f in findings[:limit]:
        lines.append(f"- [{f.rule}] «{f.quote}»" + (f" ({f.detail})" if f.detail else "") + f": {RULES[f.rule]}")
    if len(findings) > limit:
        lines.append(f"- … and {len(findings) - limit} more of the same kinds.")
    return "\n".join(lines)


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
        words += len(spoken_words(MARKER_RE.sub(" ", script[pos:m.start()])))
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
