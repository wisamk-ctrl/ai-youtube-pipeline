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

from pipeline.script_format import Cue, extract_cues, spoken_text

log = logging.getLogger(__name__)

CARD_HTML = """<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8">
<style>
@font-face {{ font-family: Kufi; src: url("{font}"); }}
html,body {{ margin:0; width:{w}px; height:{h}px; background:transparent; }}
.card {{ position:absolute; right:96px; bottom:{bottom}px; max-width:{maxw}px; padding:22px 36px;
  background:rgba(11,18,32,.82); border-right:10px solid #E8B24A; border-radius:8px;
  color:#F4F1EA; font:{size}px/1.45 Kufi, "Noto Kufi Arabic", sans-serif; }}
.small {{ font-size:{small}px; opacity:.85; }}
.tag {{ display:inline-block; font-size:22px; color:#0B1220; background:#E8B24A; border-radius:4px;
  padding:2px 12px; margin-bottom:10px; }}
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


def render_card(text: str, dest: Path, kind: str = "onscreen", width: int = 1920, height: int = 1080) -> Path:
    """Render one transparent PNG card with Playwright/Chromium."""
    from playwright.sync_api import sync_playwright  # lazy: only the post phase needs it

    small = kind != "onscreen"
    page_html = CARD_HTML.format(
        font=_font_path(), w=width, h=height, bottom=int(height * 0.16) if not small else int(height * 0.05),
        maxw=int(width * 0.62), size=int(height * 0.052), small=int(height * 0.028),
        cls="small" if small else "", tag='<div class="tag">B-ROLL</div><br>' if small else "", text=html.escape(text))
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


def anchor(cue: Cue, script_words: list[str], srt_idx: list[tuple[float, str]], window: float = 20.0) -> float:
    """Snap the cue to the subtitle that contains the words spoken just before it, if one is near the estimate."""
    if not srt_idx or cue.at_word < 3:
        return cue.at_seconds
    probe = " ".join(script_words[max(0, cue.at_word - 3):cue.at_word])
    best = None
    for t, text in srt_idx:
        if abs(t - cue.at_seconds) <= window and probe and probe in text:
            best = t if best is None or abs(t - cue.at_seconds) < abs(best - cue.at_seconds) else best
    return best if best is not None else cue.at_seconds


def plan_cards(script: str, wpm: int, out_dir: Path, srt: Path | None = None,
               card_seconds: float = 6.0, broll_seconds: float = 4.0,
               kinds: tuple[str, ...] = ("onscreen", "broll")) -> list[Card]:
    cues = [c for c in extract_cues(script, wpm) if c.kind in kinds]
    words = spoken_text(script).split()
    idx = _srt_index(srt)
    cards: list[Card] = []
    for n, c in enumerate(cues, 1):
        png = out_dir / "cards" / f"card_{n:02d}_{c.kind}.png"
        cards.append(Card(c, anchor(c, words, idx), card_seconds if c.kind == "onscreen" else broll_seconds, png))
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


def run_overlays(video: Path, script: str, cfg: dict[str, Any], out_dir: Path, srt: Path | None = None,
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
    for c in cards:
        render_card(c.cue.text, c.png, c.cue.kind)
    (out_dir / "cards.json").write_text(json.dumps(
        [{"kind": c.cue.kind, "text": c.cue.text, "at": round(c.at, 2), "seconds": c.seconds, "png": c.png.name} for c in cards],
        ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Overlaying %d cue cards (%d on-screen, %d b-roll markers)", len(cards),
             sum(c.cue.kind == "onscreen" for c in cards), sum(c.cue.kind == "broll" for c in cards))
    return overlay(video, cards, out_dir / "with_cards.mp4")
