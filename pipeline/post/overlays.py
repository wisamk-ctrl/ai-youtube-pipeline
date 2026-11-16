"""
On-screen cue cards — the first consumer of the script's production markers.

The writer emits [On-Screen Text: …] and [Show B-Roll: …] cues and the cue sheet gives each an
estimated timestamp. This module renders every On-Screen Text cue as a lower-third card (Arabic
type, brand colours, code-rendered with the same Chromium the sting uses) and overlays it on the
talking-head video for `card_seconds` from its timestamp. B-Roll cues become a small corner
caption with the description, so the editor sees where footage belongs until real B-roll exists.

Timing comes from words-per-minute, so cards drift by a few seconds across the episode; the
subtitle timestamps from Whisper are used to re-anchor each cue when available (the cue's
preceding words are searched in the SRT and the card snaps to that time).
"""

from __future__ import annotations

import html
import json
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.script_format import Cue, extract_cues, spoken_text, spoken_words

log = logging.getLogger(__name__)

CARD_HTML = """<!doctype html><html dir="{dir}"><meta charset="utf-8">
<style>
@font-face {{ font-family: Kufi; src: url("{font}"); }}
{fonts}
html,body {{ margin:0; width:{w}px; height:{h}px; background:transparent; }}
.card {{ position:absolute; {side}:96px; bottom:{bottom}px; max-width:{maxw}px; padding:20px 34px;
  background:rgba(20,17,15,.93); border-{side}:10px solid #E5432A;
  color:#F3EEE3; font:600 {size}px/1.35 Sans, Kufi, "Noto Kufi Arabic", sans-serif; }}
.small {{ font-size:{small}px; opacity:.9; }}
.question {{ font:700 {size}px/1.25 Display, Kufi, serif; letter-spacing:-.01em; }}
.topic {{ bottom:auto; top:{top}px; {side}:{edge}px; padding:12px 20px; font:700 {chip}px/1 Mono, Kufi, monospace;
  letter-spacing:.12em; text-transform:uppercase; border-{side}-width:8px; background:#14110F; }}
.tag {{ display:inline-block; font:700 20px/1 Mono, monospace; letter-spacing:.12em; color:#F3EEE3; background:#E5432A;
  padding:5px 12px; margin-bottom:10px; }}
</style><body><div class="card {cls}">{tag}{text}</div></body></html>"""


@dataclass
class Card:
    cue: Cue
    at: float
    seconds: float
    png: Path


def _font_path() -> str:
    for p in (Path("lowerthird/fonts/display.ttf"), Path("sting/fonts/display.ttf")):
        if p.exists():
            return p.resolve().as_uri()
    return ""


def _brand_fonts() -> str:
    """The brand's faces embedded in the page (a file link is not reliably loaded by set_content)."""
    from pipeline.post.visual_assets import _fonts
    return _fonts()


def render_card(text: str, dest: Path, kind: str = "onscreen", width: int = 1920, height: int = 1080) -> Path:
    """Render one transparent PNG card with Playwright/Chromium."""
    from playwright.sync_api import sync_playwright  # lazy: only the post phase needs it

    from pipeline.language import ui
    rtl = ui("dir") == "rtl"
    small = kind == "broll"
    page_html = CARD_HTML.format(
        dir=ui("dir"), side="right" if rtl else "left",
        font=_font_path(), fonts=_brand_fonts(), w=width, h=height, bottom=int(height * 0.05) if kind == "broll" else int(height * 0.17),   # just above the captions
        maxw=int(width * (0.5 if kind == "topic" else 0.62)), size=int(height * 0.052), small=int(height * 0.028),
        top=int(height * 0.055), edge=int(width * 0.04), chip=int(height * 0.022),
        cls="small" if small else kind if kind in ("topic", "question") else "",
        tag='<div class="tag">B-ROLL</div><br>' if kind == "broll" else "", text=html.escape(text))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": width, "height": height})
        pg.set_content(page_html, wait_until="networkidle")
        pg.screenshot(path=str(dest), omit_background=True)
        b.close()
    return dest


def _srt_index(srt: Path | None) -> list[tuple[float, str]]:
    if not srt or not srt.exists():
        return []
    out, t, buf = [], None, []
    for line in srt.read_text(encoding="utf-8").splitlines() + [""]:
        m = re.match(r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d) -->", line)
        if m:
            t = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1000
        elif line.strip() == "" and t is not None:
            out.append((t, " ".join(buf))); t, buf = None, []
        elif t is not None and not line.strip().isdigit():
            buf.append(line.strip())
    return out


def _norm(word: str) -> str:
    return re.sub(r"[^\w]", "", word, flags=re.UNICODE).lower()


def _heard(srt_idx: list[tuple[float, str]]) -> list[tuple[float, str]]:
    """Every caption word with its own time, spread evenly from its caption's start to the next one's."""
    out = []
    for k, (t, text) in enumerate(srt_idx):
        ws = [w for w in (_norm(x) for x in text.split()) if w]
        end = srt_idx[k + 1][0] if k + 1 < len(srt_idx) else t + 0.4 * len(ws)
        out += [(t + (end - t) * n / max(1, len(ws)), w) for n, w in enumerate(ws)]
    return out


def locate(at_word: int, script_words: list[str], srt_idx: list[tuple[float, str]], fallback: float,
           window: float = 45.0) -> float:
    """When script word number `at_word` is heard. The first guess is its share of the way through the
    captions (the real pace, not a words-per-minute setting: W46-en ran 12% faster than the setting and
    every label came late). It is then snapped to the words around it in the captions, matched
    without case or punctuation and across caption breaks."""
    heard = _heard(srt_idx)
    if not heard or not script_words:
        return fallback
    est = heard[0][0] + (heard[-1][0] - heard[0][0]) * min(1.0, at_word / len(script_words))
    sw = [_norm(w) for w in script_words]
    hw = [w for _, w in heard]
    # (probe, where the cue sits inside it): the words after the cue, then the words before it
    probes = [(sw[at_word:at_word + n], 0) for n in (4, 3)] + [(sw[max(0, at_word - n):at_word], n) for n in (4, 3)]
    for probe, lead in probes:
        probe = [w for w in probe if w]
        if len(probe) < 3:
            continue
        hits = [k for k in range(len(hw) - len(probe) + 1) if hw[k:k + len(probe)] == probe]
        hits = [min(k + min(lead, len(probe)), len(heard) - 1) for k in hits]
        near = [heard[k][0] for k in hits if abs(heard[k][0] - est) <= window]
        if near:
            return min(near, key=lambda t: abs(t - est))
    return est


def anchor(cue: Cue, script_words: list[str], srt_idx: list[tuple[float, str]], window: float = 45.0) -> float:
    """The cue's time in the video: where its place in the script is heard (see `locate`)."""
    return locate(cue.at_word, script_words, srt_idx, cue.at_seconds, window)


def plan_cards(script: str, wpm: int, out_dir: Path, srt: Path | None = None,
               card_seconds: float = 6.0, broll_seconds: float = 4.0,
               kinds: tuple[str, ...] = ("onscreen", "broll")) -> list[Card]:
    cues = [c for c in extract_cues(script, wpm) if c.kind in kinds]
    words = spoken_words(spoken_text(script))
    idx = _srt_index(srt)
    cards: list[Card] = []
    for n, c in enumerate(cues, 1):
        png = out_dir / "cards" / f"card_{n:02d}_{c.kind}.png"
        at = anchor(c, words, idx)
        at = max([t for t, _ in idx if t <= at], default=at)   # with the caption that says it, not after it
        cards.append(Card(c, at, card_seconds if c.kind == "onscreen" else broll_seconds, png))
    return cards


_QUESTION_END = ("?", "؟")
_SENT = re.compile(r"(?<=[.!?؟…])\s+")


def guide_cards(script: str, wpm: int, out_dir: Path, srt: Path | None, total: float,
                o: dict[str, Any]) -> list[Card]:
    """On-screen signposts for viewers who follow by reading (first viewers' feedback, 2026-11-12):

    - topic: each [Section] title as a small chip in the top corner for the whole section (the
      first section, the cold open, has none);
    - question: a question the script puts just before a [Pause] («Why does this matter here?»),
      as a lower-third while it is asked and through the pause."""
    from pipeline.script_format import MARKER_RE, PAUSE_RE
    words = spoken_words(spoken_text(script))
    idx = _srt_index(srt)
    cards: list[Card] = []
    if o.get("topics", True):
        secs = [c for c in extract_cues(script, wpm) if c.kind == "section"][1:]
        times = [anchor(c, words, idx) for c in secs]
        for n, (c, t) in enumerate(zip(secs, times)):
            end = times[n + 1] if n + 1 < len(times) else total
            if end - t >= 3 and c.text:
                cards.append(Card(Cue("topic", c.text, c.at_word, t), t + 0.4, end - t - 0.8,
                                  out_dir / "cards" / f"topic_{n + 1:02d}.png"))
    if o.get("questions", True):
        pos = count = n = 0
        for m in MARKER_RE.finditer(script):
            chunk = script[pos:m.start()]
            before = count
            count += len(spoken_words(chunk))
            pos = m.end()
            sents = [x.strip() for x in _SENT.split(chunk.strip()) if x.strip()]
            if not sents or not PAUSE_RE.match(m.group("body").strip()) or not sents[-1].endswith(_QUESTION_END):
                continue
            q = sents[-1]
            size = len(spoken_words(q))
            if not 3 <= size <= 16:
                continue
            n += 1
            cue = Cue("question", q, count - size, round((count - size) / wpm * 60, 1))
            cards.append(Card(cue, anchor(cue, words, idx), max(3.0, size / wpm * 60 + 1.0),
                              out_dir / "cards" / f"question_{n:02d}.png"))
    return cards


def overlay(video: Path, cards: list[Card], dest: Path) -> Path:
    """One ffmpeg pass: each card is an input overlaid between its start and end time."""
    if not cards:
        log.info("No cue cards to overlay")
        return video
    args = ["ffmpeg", "-y", "-i", str(video)]
    for c in cards:
        args += ["-i", str(c.png)]
    chain, prev = [], "0:v"
    for i, c in enumerate(cards, 1):
        out = f"v{i}"
        chain.append(f"[{prev}][{i}:v]overlay=0:0:enable='between(t,{c.at:.2f},{c.at + c.seconds:.2f})'[{out}]")
        prev = out
    args += ["-filter_complex", ";".join(chain), "-map", f"[{prev}]", "-map", "0:a?", "-c:a", "copy",
             "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(dest)]
    subprocess.run(args, check=True, capture_output=True)
    return dest


DISCLOSURE_TEXT = "توأم رقمي لوسام — بموافقة وسام"


def disclosure_card(cards: list[Card], d: dict[str, Any], out_dir: Path) -> Card | None:
    """The AI-twin disclosure lower-third inside the first minute (review 2026-11-07, Tier 1 #11):
    at `at` seconds, moved past any cue card it would sit on, never later than 60 s."""
    if not d.get("enabled", True):
        return None
    secs, at = float(d.get("seconds", 6)), float(d.get("at", 4))
    for c in sorted(cards, key=lambda c: c.at):
        if c.at < at + secs and at < c.at + c.seconds:
            at = c.at + c.seconds + 0.5
    at = min(at, 60.0 - secs)
    from pipeline.language import _current, ui
    text = str(d.get("text") or DISCLOSURE_TEXT) if _current == "ar" else str(d.get(f"text_{_current}") or ui("disclosure"))
    cue = Cue(kind="disclosure", text=text, at_word=0, at_seconds=at)
    return Card(cue, at, secs, out_dir / "cards" / "card_00_disclosure.png")


def run_overlays(video: Path, script: str, cfg: dict[str, Any], out_dir: Path, srt: Path | None = None,
                 face: list[tuple[float, float]] | None = None,
                 skip_spans: list[tuple[float, float]] | None = None) -> Path:
    """With the visual edit on, B-roll placeholders are gone (real footage replaced them) and a
    lower-third is skipped where a full-screen card already shows the same moment."""
    o = cfg.get("post", {}).get("overlays", {})
    edited = cfg.get("visuals", {}).get("enabled", False)
    cards = plan_cards(script, cfg["scripting"]["words_per_minute"], out_dir, srt,
                       float(o.get("card_seconds", 6)), float(o.get("broll_seconds", 4)),
                       ("onscreen",) if edited else ("onscreen", "broll"))
    if skip_spans:
        cards = [c for c in cards if not any(a - 0.5 <= c.at <= b for a, b in skip_spans)]
    g = o.get("guide", {})
    if g.get("enabled", True):
        from pipeline.post.edit import duration
        guides = guide_cards(script, cfg["scripting"]["words_per_minute"], out_dir, srt, duration(video), g)
        busy = [(c.at, c.at + c.seconds) for c in cards]
        for c in guides:   # a question never sits on a cue card or a full-screen card; a topic chip always shows
            if c.cue.kind == "question":
                # never over the presenter (the face spans carry their own headline frame), a card, or a full-screen card
                if any(a < c.at + c.seconds and c.at < b for a, b in busy + list(skip_spans or []) + list(face or [])):
                    continue
                busy.append((c.at, c.at + c.seconds))      # nor on the question before it
            cards.append(c)
    d = disclosure_card([c for c in cards if c.cue.kind != "topic"], o.get("disclosure", {}), out_dir)
    if d:   # compliance: never dropped for a full-screen card
        cards = sorted(cards + [d], key=lambda c: c.at)
    for c in cards:
        render_card(c.cue.text, c.png, c.cue.kind)
    (out_dir / "cards.json").write_text(json.dumps(
        [{"kind": c.cue.kind, "text": c.cue.text, "at": round(c.at, 2), "seconds": c.seconds, "png": c.png.name} for c in cards],
        ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Overlaying %d cue cards (%d on-screen, %d b-roll markers, %d topic chips, %d questions)", len(cards),
             sum(c.cue.kind == "onscreen" for c in cards), sum(c.cue.kind == "broll" for c in cards),
             sum(c.cue.kind == "topic" for c in cards), sum(c.cue.kind == "question" for c in cards))
    return overlay(video, cards, out_dir / "with_cards.mp4")
