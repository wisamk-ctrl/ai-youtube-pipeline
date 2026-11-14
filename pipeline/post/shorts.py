"""
Native 9:16 Shorts from the edited episode (review 2026-11-07, Tier 2: the old centre crop cut
the cards in half).

Picking (when no spans are given): 2–3 story sections of the script, each cut from the section's
first sentence to a sentence end, 30–58 s, one story each. The cold open, the outro and a
quick-fire round (several stories) are never used. Times come from the script-exact captions:
every sentence starts a new caption (script_captions flushes on a sentence end), so a sentence is
found by the caption that begins with its first words.

Layout, 1080×1920:
    top band     big Arabic title (the section's own title from the script)
    middle band  the edit's picture for that span, scaled to the full width
    behind both  the same picture, blurred and darkened, filling the frame
    lower band   the captions (script-exact)
    last 2 s     «الحلقة الكاملة على القناة» card, the voice already finished

Each Short varies slightly (title position, colour, band position) so a channel of Shorts does
not read as one template (YouTube's 2025 "inauthentic / mass-produced" rule).

Outputs output/<week>/shorts/short_NN.mp4 and shorts/shorts.json.
"""

from __future__ import annotations

import html
import json
import logging
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pipeline.language import ui
from pipeline.post.visual_assets import GOLD, NAVY, SAND, _fonts
from pipeline.script_format import MARKER_RE, caption_text, spoken_text, spoken_words

log = logging.getLogger(__name__)

W, H = 1080, 1920
CARD_SECONDS = 2.0
SENTENCE_END = (".", "؟", "?", "!", "…")
SKIP_TITLES = ("سريع", "سريعة", "quick", "خلاصة", "ختام", "الختام")   # quick-fire rounds, outros

# Per-Short variations: (title band top as a share of the top band, title colour, title backing,
# middle band offset in px from centre). Cycled, so Shorts 1–3 of an episode all differ.
VARIANTS = [
    {"title_top": 0.30, "color": SAND, "pill": "rgba(11,18,32,.0)", "bar": GOLD, "mid": 0},
    {"title_top": 0.42, "color": NAVY, "pill": GOLD, "bar": SAND, "mid": -60},
    {"title_top": 0.22, "color": GOLD, "pill": "rgba(11,18,32,.72)", "bar": SAND, "mid": 60},
]


@dataclass
class Span:
    title: str
    start: float
    end: float


@dataclass
class _Sentence:
    words: list[str]          # caption-form words
    start: float | None = None


# ── Picking ─────────────────────────────────────────────────────────────────
def _sections(script: str) -> list[tuple[str, str]]:
    """(title, body) per [Section]; text before the first section is ignored."""
    out: list[tuple[str, str]] = []
    marks = [m for m in MARKER_RE.finditer(script) if m.group("body").strip().lower().startswith("section")]
    for k, m in enumerate(marks):
        title = m.group("body").partition(":")[2].strip()
        body = script[m.end(): marks[k + 1].start() if k + 1 < len(marks) else len(script)]
        out.append((title, body))
    return out


def _sentences(body: str) -> list[_Sentence]:
    words = [caption_text(t).strip() for t in spoken_words(spoken_text(body))]
    out, cur = [], []
    for w in words:
        cur.append(w)
        if w.endswith(SENTENCE_END):
            out.append(_Sentence(cur))
            cur = []
    if cur:
        out.append(_Sentence(cur))
    return out


def _caption_starts(srt: Path | None) -> list[tuple[float, float, str]]:
    from pipeline.post.overlays import _srt_index
    idx = _srt_index(srt)
    if not srt or not srt.exists():
        return []
    ends = [float(_ts(m[1])) for m in re.finditer(r"--> (\d\d:\d\d:\d\d[,.]\d\d\d)", srt.read_text(encoding="utf-8"))]
    return [(t, ends[k] if k < len(ends) else t, text) for k, (t, text) in enumerate(idx)]


def _ts(s: str) -> float:
    h, m, rest = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))


def _time_sentences(sents: list[_Sentence], caps: list[tuple[float, float, str]], after: float) -> float:
    """Give each sentence the start of the first caption (at or after `after`, in order) that begins
    with its first words. Returns where the search ended."""
    k = 0
    while k < len(caps) and caps[k][0] < after - 0.01:
        k += 1
    for s in sents:
        probe = " ".join(s.words[:3]).rstrip("،,.:؛;")
        for j in range(k, len(caps)):
            if probe and caps[j][2].startswith(probe):
                s.start = caps[j][0]
                k = j + 1
                break
    return caps[k - 1][0] if 0 < k <= len(caps) else after


def pick_spans(script: str, srt: Path | None, count: int = 3, min_s: float = 30.0, max_s: float = 58.0,
               target_s: float = 45.0) -> list[Span]:
    """Up to `count` one-story spans, each starting at its section's first sentence and ending at a
    sentence end, min_s ≤ length ≤ max_s (closest to target_s). In episode order."""
    caps = _caption_starts(srt)
    if not caps:
        return []
    sections = _sections(script)
    timed: list[tuple[str, list[_Sentence]]] = []
    cursor = 0.0
    for title, body in sections:
        sents = _sentences(body)
        cursor = _time_sentences(sents, caps, cursor)
        timed.append((title, sents))
    spans: list[Span] = []
    last = len(timed) - 1
    for n, (title, sents) in enumerate(timed):
        if n == 0 or (n == last and last >= 2):           # cold open, outro
            continue
        if any(k in title.lower() for k in SKIP_TITLES):
            continue
        starts = [s.start for s in sents]
        if not starts or starts[0] is None:
            continue
        # The section ends where the next one begins (or at the last caption's end).
        nxt = next((s.start for _, ss in timed[n + 1:] for s in ss if s.start is not None), caps[-1][1])
        bounds = [t for t in starts[1:] if t is not None] + [nxt]
        a = starts[0]
        ok = [b for b in bounds if min_s <= b - a <= max_s and b <= nxt + 1e-3]
        if not ok:
            continue
        b = min(ok, key=lambda x: abs((x - a) - target_s))
        spans.append(Span(title, round(a, 2), round(b - 0.05, 2)))
        if len(spans) >= count:
            break
    return spans


# ── Building ────────────────────────────────────────────────────────────────
def title_html(title: str, variant: dict[str, Any], band: int) -> str:
    """Transparent 1080×1920 page with the title in the top band."""
    size = 92 if len(title) <= 22 else 76
    return f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{W}px;height:{H}px;background:transparent;overflow:hidden}}
.t{{position:absolute;left:70px;right:70px;top:{band * variant['title_top']:.0f}px;text-align:center}}
.p{{display:inline-block;font:800 {size}px/1.3 Kufi,sans-serif;color:{variant['color']};background:{variant['pill']};
padding:.12em .45em .22em;border-radius:.35em;text-shadow:0 4px 18px rgba(0,0,0,.45)}}
.bar{{width:150px;height:12px;margin:34px auto 0;background:{variant['bar']};border-radius:9px}}
.show{{position:absolute;top:70px;left:0;right:0;text-align:center;font:600 34px Kufi,sans-serif;color:{GOLD};opacity:.9}}
</style></head><body><div class="show" dir="{ui("dir")}">{ui("show")}</div>
<div class="t"><div class="p" dir="{ui("dir")}">{html.escape(title)}</div><div class="bar"></div></div></body></html>"""


def end_html(show: str) -> str:
    return f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:radial-gradient(120% 80% at 50% 35%,#16213a 0%,{NAVY} 60%,#070b14 100%);color:{SAND};
display:flex;flex-direction:column;align-items:center;justify-content:center;gap:48px;font-family:Kufi,sans-serif}}
.a{{font:800 96px/1.3 Kufi,sans-serif;text-align:center;max-width:900px}}
.b{{font:800 54px Kufi,sans-serif;color:{NAVY};background:{GOLD};padding:.15em .8em .25em;border-radius:.5em}}
</style></head><body dir="{ui("dir")}"><div class="a">{ui("full")}</div><div class="b">{html.escape(show)}</div></body></html>"""


def _short_srt(srt: Path, a: float, b: float, dest: Path) -> Path:
    """The captions inside [a, b], moved to start at 0, Latin runs isolated for libass."""
    from pipeline.post.subtitles import isolate_latin
    blocks = re.split(r"\n\s*\n", srt.read_text(encoding="utf-8").strip())
    out, n = [], 0
    for blk in blocks:
        lines = blk.splitlines()
        m = next((re.match(r"(\S+) --> (\S+)", ln) for ln in lines if "-->" in ln), None)
        if not m:
            continue
        t0, t1 = _ts(m[1]), _ts(m[2])
        if t1 <= a or t0 >= b:
            continue
        text = [isolate_latin(ln) for ln in lines[lines.index(m.string) + 1:] if ln.strip()]
        n += 1
        out += [str(n), f"{_fmt(max(0.0, t0 - a))} --> {_fmt(min(b, t1) - a)}", *text, ""]
    dest.write_text("\n".join(out), encoding="utf-8")
    return dest


def _fmt(x: float) -> str:
    ms = int(round(max(0.0, x) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def filter_graph(span_s: float, mid_y: int, srt: Path | None, font: str, fps: int = 30) -> str:
    """[0]=edit span, [1]=title PNG, [2]=end card PNG → [v], [a]."""
    mid_h = round(W * 9 / 16 / 2) * 2                        # 608: the 16:9 picture at full width
    g = [f"[0:v]fps={fps},setsar=1,split=2[a][b]",
         f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,eq=brightness=-0.18:saturation=0.8[bg]",
         f"[b]scale={W}:{mid_h}[mid]",
         f"[bg][mid]overlay=0:{mid_y}[m1]",
         "[m1][1:v]overlay=0:0:shortest=1[m2]"]
    last = "m2"
    if srt:
        path = str(srt).replace("\\", "\\\\").replace(":", "\\:")
        style = (f"PlayResX={W},PlayResY={H},FontName={font},FontSize=64,PrimaryColour=&H00F4F1EA,BorderStyle=3,"
                 f"Outline=12,OutlineColour=&H50201209,BackColour=&H50201209,Shadow=0,Alignment=2,"
                 f"MarginV={H - (mid_y + mid_h) - 330},MarginL=80,MarginR=80")
        g.append(f"[m2]subtitles='{path}':original_size={W}x{H}:force_style='{style}'[m3]")
        last = "m3"
    g.append(f"[{last}]tpad=stop_mode=clone:stop_duration={CARD_SECONDS}[m4]")
    g.append(f"[m4][2:v]overlay=0:0:shortest=1:enable='gte(t,{span_s:.3f})',format=yuv420p[v]")
    g.append(f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,afade=t=out:st={max(0.0, span_s - 0.25):.3f}:d=0.25,"
             f"apad=pad_dur={CARD_SECONDS},loudnorm=I=-14:TP=-1.5:LRA=7[a]")
    return ";".join(g)


def build(video: Path, script: str, srt: Path | None, spans_arg: list[tuple[float, float]] | None,
          cfg: dict[str, Any], out_dir: Path, sting: tuple[float, float] | None = None) -> list[dict[str, Any]]:
    """Make the week's Shorts from the edited cut (picture + voice, before captions and sting)."""
    s = cfg.get("post", {}).get("shorts", {})
    if not s.get("enabled", True) and not spans_arg:
        return []
    if spans_arg:
        spans = [Span(f"قصة {k}", a, b) for k, (a, b) in enumerate(spans_arg, 1)]
        named = pick_spans(script, srt, count=99, min_s=0, max_s=1e9)
        for sp in spans:   # a chosen span takes the title of the section it starts in, if known
            near = [p for p in named if p.start <= sp.start + 0.5]
            if near:
                sp.title = near[-1].title
    else:
        spans = pick_spans(script, srt, int(s.get("count", 3)), float(s.get("min_seconds", 30)),
                           float(s.get("max_seconds", 58)))
    if not spans:
        log.info("Shorts: no span of 30–60 s on one story found")
        return []
    from pipeline.post.packaging import _show_name, to_final
    from pipeline.post.subtitles import _font, _ffmpeg
    from pipeline.post.visual_assets import Renderer
    fps = int(cfg.get("visuals", {}).get("fps", 30))
    dest_dir = out_dir / "shorts"
    dest_dir.mkdir(parents=True, exist_ok=True)
    made: list[dict[str, Any]] = []
    mid_h = round(W * 9 / 16 / 2) * 2
    with Renderer(W, H) as r:
        end_png = dest_dir / "end_card.png"
        r.still(end_html(_show_name(cfg)), end_png)
        for k, sp in enumerate(spans, 1):
            var = VARIANTS[(k - 1) % len(VARIANTS)]
            mid_y = (H - mid_h) // 2 + int(var["mid"])
            title_png = dest_dir / f"title_{k:02d}.png"
            r.page.set_content(title_html(sp.title, var, mid_y), wait_until="load")
            r.page.evaluate("document.fonts.ready")
            r.page.screenshot(path=str(title_png), omit_background=True)
            span_s = sp.end - sp.start
            sub = _short_srt(srt, sp.start, sp.end, dest_dir / f"short_{k:02d}.srt") if srt and srt.exists() else None
            dest = dest_dir / f"short_{k:02d}.mp4"
            _ffmpeg("-ss", f"{sp.start:.3f}", "-t", f"{span_s:.3f}", "-i", str(video),
                    "-loop", "1", "-i", str(title_png), "-loop", "1", "-i", str(end_png),
                    "-filter_complex", filter_graph(span_s, mid_y, sub, _font(), fps),
                    "-map", "[v]", "-map", "[a]", "-t", f"{span_s + CARD_SECONDS:.3f}",
                    "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(fps),
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", str(dest))
            for p in (title_png, sub):
                if p:
                    p.unlink(missing_ok=True)
            made.append(dict(asdict(sp), file=dest.name, episode_start=round(to_final(sp.start, sting), 2)))
        end_png.unlink(missing_ok=True)
    (dest_dir / "shorts.json").write_text(json.dumps(made, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Shorts: %d made → %s", len(made), dest_dir)
    return made
