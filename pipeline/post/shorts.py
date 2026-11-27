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
from pipeline.post.visual_assets import DISPLAY, GOLD, MONO, NAVY, SAND, TEXT, _fonts
from pipeline.script_format import MARKER_RE, caption_text, spoken_text, spoken_words

log = logging.getLogger(__name__)

W, H = 1080, 1920
CARD_SECONDS = 2.0
OUTRO = Path(__file__).resolve().parents[2] / "assets" / "brand" / "shorts_outro_en.wav"   # "For the full story…"
SENTENCE_END = (".", "؟", "?", "!", "…")
SKIP_TITLES = ("سريع", "سريعة", "quick", "خلاصة", "ختام", "الختام")   # quick-fire rounds, outros

# Per-Short variations: (title band top as a share of the top band, title colour, title backing,
# middle band offset in px from centre). Cycled, so Shorts 1–3 of an episode all differ.
VARIANTS = [
    {"title_top": 0.30, "color": SAND, "pill": "rgba(30,10,71,.0)", "bar": GOLD, "mid": 0},
    {"title_top": 0.42, "color": NAVY, "pill": GOLD, "bar": SAND, "mid": -60},
    {"title_top": 0.22, "color": GOLD, "pill": "rgba(30,10,71,.9)", "bar": SAND, "mid": 60},
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
               target_s: float = 45.0, skip_intro: frozenset[str] = frozenset()) -> list[Span]:
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
        # A Short with its own opening line starts on the story's second sentence: the first is the
        # episode's hand-over ("From the US to Saudi Arabia…"), which reads as a clip of something longer.
        if title.strip().lower() in skip_intro and len(bounds) > 2:
            a, bounds = bounds[0], bounds[1:]
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
.p{{display:inline-block;font:800 {size}px/1.08 {DISPLAY};letter-spacing:-.03em;color:{variant['color']};background:{variant['pill']};
padding:.12em .45em .22em;border-radius:.35em;text-shadow:0 4px 18px rgba(0,0,0,.45)}}
.bar{{width:150px;height:12px;margin:34px auto 0;background:{variant['bar']};border-radius:9px}}
.show{{position:absolute;top:70px;left:0;right:0;text-align:center;font:700 28px {MONO};letter-spacing:.14em;text-transform:uppercase;color:{SAND}}}
</style></head><body><div class="show" dir="{ui("dir")}">{ui("show")}</div>
<div class="t"><div class="p" dir="{ui("dir")}">{html.escape(title)}</div><div class="bar"></div></div></body></html>"""


def end_html(show: str, text: str | None = None, ask: str | None = None) -> str:
    """The closing card. A Short that asks (founder 2026-11-27) shows its question and invites the answer."""
    if ask:
        size = 96 if len(ask) <= 40 else 80 if len(ask) <= 60 else 68
        return f"""<!doctype html><html><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:{NAVY};color:{SAND};display:flex;flex-direction:column;align-items:center;justify-content:center;
gap:56px;padding:0 84px;box-sizing:border-box;font-family:{TEXT}}}
.q{{font:800 {size}px/1.08 {DISPLAY};letter-spacing:-.03em;text-align:center}}
.c{{font:700 52px {TEXT};color:{GOLD};text-align:center}}
.b{{font:700 46px {TEXT};color:{NAVY};background:{GOLD};padding:.3em 1em .36em}}
</style></head><body dir="{ui("dir")}"><div class="q">{html.escape(ask)}</div>
<div class="c">{html.escape(ui("answer_below"))}</div><div class="b">{html.escape(show)}</div></body></html>"""
    return f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:{NAVY};color:{SAND};
display:flex;flex-direction:column;align-items:center;justify-content:center;gap:48px;font-family:{TEXT}}}
.a{{font:800 104px/1.05 {DISPLAY};letter-spacing:-.035em;text-align:center;max-width:900px}}
.b{{font:700 46px {TEXT};color:{NAVY};background:{GOLD};padding:.3em 1em .36em}}
</style></head><body dir="{ui("dir")}"><div class="a">{html.escape(text) if text else ui("full")}</div><div class="b">{html.escape(show)}</div></body></html>"""


HOOK_SECONDS = 2.5


def hook_html(hook: str, show: str) -> str:
    """The Short's own opening: one newly written line, full screen, before the episode's picture starts
    (monetisation playbook: a Short is a re-edit with a new opening, never a straight cut)."""
    size = 124 if len(hook) <= 32 else 100 if len(hook) <= 52 else 84
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:{NAVY};color:{SAND};display:flex;flex-direction:column;justify-content:center;gap:56px;
padding:0 84px;box-sizing:border-box;font-family:{TEXT}}}
.k{{font:700 40px {TEXT};color:{GOLD};letter-spacing:.02em}}
.h{{font:800 {size}px/1.06 {DISPLAY};letter-spacing:-.035em}}
.bar{{width:200px;height:12px;background:{GOLD}}}
</style></head><body dir="{ui("dir")}"><div class="k">{html.escape(show)}</div><div class="h">{html.escape(hook)}</div><div class="bar"></div></body></html>"""


def hook_overlay_html(hook: str, mid_y: int) -> str:
    """The opening line as a band over the story's picture, for its first seconds while the voice already runs
    (founder 2026-11-24): the Short still opens with its own new line, but nobody waits through a card."""
    size = 96 if len(hook) <= 32 else 80 if len(hook) <= 52 else 68
    mid_h = round(W * 9 / 16 / 2) * 2
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{W}px;height:{H}px;background:transparent;overflow:hidden}}
.b{{position:absolute;left:0;right:0;top:{mid_y + mid_h // 2}px;transform:translateY(-50%);background:rgba(11,22,40,.86);
padding:44px 72px;box-sizing:border-box;color:{SAND};font:800 {size}px/1.06 {DISPLAY};letter-spacing:-.03em;
border-top:10px solid {GOLD}}}
</style></head><body dir="{ui("dir")}"><div class="b">{html.escape(hook)}</div></body></html>"""


def hooks_for(out_dir: Path) -> dict[str, str]:
    """Opening lines by section title: the founder's `reviewed/<week>/shorts.yaml` first, then the plan's
    `short_hooks` (written with the title options). A section with no line gets no opening card."""
    found: dict[str, str] = {}
    plan = out_dir / "plan.json"
    if plan.exists():
        for h in json.loads(plan.read_text(encoding="utf-8")).get("short_hooks") or []:
            found[str(h.get("section", "")).strip().lower()] = str(h.get("hook", "")).strip()
    own = Path(__file__).resolve().parents[2] / "reviewed" / out_dir.name / "shorts.yaml"
    if own.exists():
        import yaml
        for k, v in ((yaml.safe_load(own.read_text(encoding="utf-8")) or {}).get("hooks") or {}).items():
            found[str(k).strip().lower()] = str(v).strip()
    return {k: v for k, v in found.items() if k and v}


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


SRC_W, SRC_H = 1920, 1080          # the uniform clip each Short is built from
ENCODE_LIMIT = 600                 # seconds one ffmpeg call may take; a Short is under a minute long


def _timed(*args: str) -> bool:
    """ffmpeg with a time limit: a stalled encode is logged and skipped instead of holding the whole run."""
    try:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True, timeout=ENCODE_LIMIT)
        return True
    except subprocess.TimeoutExpired:
        log.error("Shorts: ffmpeg passed %d s and was stopped: %s", ENCODE_LIMIT, " ".join(args)[:1500])
        return False


def filter_graph(span_s: float, mid_y: int, srt: Path | None, font: str, fps: int = 30, hook: float = 0.0,
                 bed: tuple[int, float] | None = None, voice_gain: float | None = None,
                 card: float = CARD_SECONDS, outro: tuple[int, float] | None = None, overlay: float = 0.0) -> str:
    """[0]=edit span, [1]=title PNG, [2]=end card PNG, with a hook also [3]=hook PNG and [4]=chime → [v], [a].
    hook: a full-screen card for that long before the voice; overlay: the hook PNG over the first seconds of the
    story instead, the voice starting at once and no chime."""
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
    lead = f"start_mode=clone:start_duration={hook}:" if hook else ""
    g.append(f"[{last}]tpad={lead}stop_mode=clone:stop_duration={card}[m4]")
    end = f"[m4][2:v]overlay=0:0:shortest=1:enable='gte(t,{hook + span_s:.3f})'"
    # The voice is levelled on its own, then the rest is laid under it at fixed levels: levelling the mix
    # made the voice dip after the chime. `bed` = (input index, gain in dB) of our generated music, which
    # carries the script's pauses (W46-en: a Short went silent for 2 s twice; the edit it is cut from has
    # no music yet).
    total = hook + span_s + card
    # One fixed gain from the span's measured loudness: a levelling filter that follows the signal lifted
    # the voice after each pause.
    level = f"volume={voice_gain:.2f}dB" if voice_gain is not None else "loudnorm=I=-14:TP=-1.5:LRA=7"
    g.append(f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,afade=t=out:st={max(0.0, span_s - 0.25):.3f}:d=0.25,"
             f"{level},apad=pad_dur={card}" + (f",adelay={int(hook * 1000)}:all=1" if hook else "") + "[sp]")
    mix = ["[sp]"]
    if hook:
        g.append(f"{end}[m5]")
        g.append(f"[m5][3:v]overlay=0:0:shortest=1:enable='lt(t,{hook})',format=yuv420p[v]")
        g.append("[4:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=-6dB,adelay=150:all=1[ch]")
        mix.append("[ch]")
    elif overlay:
        g.append(f"{end}[m5]")
        g.append(f"[m5][3:v]overlay=0:0:shortest=1:enable='lt(t,{overlay})',format=yuv420p[v]")
    else:
        g.append(f"{end},format=yuv420p[v]")
    if outro is not None:   # the spoken pointer to the episode, over the end card (founder 2026-11-18)
        g.append(f"[{outro[0]}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={outro[1]:.2f}dB,"
                 f"adelay={int((hook + span_s + 0.3) * 1000)}:all=1[ou]")
        mix.append("[ou]")
    if bed:
        g.append(f"[{bed[0]}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,"
                 f"volume={bed[1]:.2f}dB,afade=t=in:d=0.4,afade=t=out:st={max(0.0, total - 1.5):.3f}:d=1.5[bd]")
        mix.append("[bd]")
    g.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,alimiter=limit=0.7:level=0[a]" if len(mix) > 1
             else "[sp]alimiter=limit=0.7:level=0[a]")
    return ";".join(g)


def build(video: Path, script: str, srt: Path | None, spans_arg: list[tuple[float, float]] | None,
          cfg: dict[str, Any], out_dir: Path, sting: tuple[float, float] | None = None,
          breaking: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Make the week's Shorts from the edited cut (picture + voice, before captions and sting).

    `breaking` (a news Short made the day the story breaks, founder 2026-11-18): {"title", "end_text",
    "outro"}: one Short over the whole cut, its own end card line and spoken outro ("more on Sunday")."""
    s = cfg.get("post", {}).get("shorts", {})
    if not s.get("enabled", True) and not spans_arg:
        return []
    if breaking:
        spans = [Span(str(breaking["title"]), a, b) for a, b in spans_arg or []]
    elif spans_arg:
        spans = [Span(f"قصة {k}", a, b) for k, (a, b) in enumerate(spans_arg, 1)]
        named = pick_spans(script, srt, count=99, min_s=0, max_s=1e9)
        for sp in spans:   # a chosen span takes the title of the section it starts in, if known
            near = [p for p in named if p.start <= sp.start + 0.5]
            if near:
                sp.title = near[-1].title
    else:
        spans = pick_spans(script, srt, int(s.get("count", 3)), float(s.get("min_seconds", 30)),
                           float(s.get("max_seconds", 58)), float(s.get("target_seconds", 45)),
                           skip_intro=frozenset(hooks_for(out_dir)))
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
        ask = str((breaking or {}).get("question") or "").strip() or None
        r.still(end_html(_show_name(cfg), (breaking or {}).get("end_text"), ask), end_png)
        hooks = hooks_for(out_dir)
        bed_wav, bed_gain = None, 0.0
        if str(cfg.get("post", {}).get("audio", {}).get("music", "generated")) == "generated":
            from pipeline.post import audio as audio_mod
            bed_wav = audio_mod.music_loop(dest_dir / "bed.wav")
            bed_gain = float(s.get("music_lufs", -30)) - audio_mod.measure(bed_wav)["input_i"]
        # The spoken pointer to the full episode (founder 2026-11-18), English weeks only for now.
        outro_s, outro_gain = 0.0, 0.0
        outro_file = Path((breaking or {}).get("outro") or OUTRO)
        if outro_file.exists() and str(cfg.get("language", "")) == "en":
            from pipeline.post import audio as audio_mod
            outro_s = audio_mod.duration_of(outro_file)
            outro_gain = min(12.0, -14.0 - audio_mod.measure(outro_file)["input_i"])
        card = max(CARD_SECONDS, outro_s + 0.9)
        chime = dest_dir / "hook_chime.wav"
        if hooks:
            from pipeline.post.audio import accent
            accent(chime)
        jobs_: list = []
        for k, sp in enumerate(spans, 1):
            var = VARIANTS[(k - 1) % len(VARIANTS)]
            mid_y = (H - mid_h) // 2 + int(var["mid"])
            title_png = dest_dir / f"title_{k:02d}.png"
            r.page.set_content(title_html(sp.title, var, mid_y), wait_until="load")
            r.page.evaluate("document.fonts.ready")
            r.page.screenshot(path=str(title_png), omit_background=True)
            # Open in the pause before the first word, not at the caption's start time: the caption ran
            # ~0.1 s late and "Anthropic" came out as "thropic" (W46-en, Short 2, founder).
            caption_start = sp.start
            try:
                from pipeline.post import audio as audio_mod
                cut = audio_mod.silence_cut(video, sp.start, before=0.8, after=0.05)
                sp.start = round(cut if cut < sp.start else max(0.0, sp.start - 0.15), 2)
            except Exception:  # noqa: BLE001
                pass
            span_s = sp.end - sp.start
            sub = _short_srt(srt, sp.start, sp.end, dest_dir / f"short_{k:02d}.srt") if srt and srt.exists() else None
            dest = dest_dir / f"short_{k:02d}.mp4"
            hook_text = hooks.get(sp.title.strip().lower(), "")
            # The span is first cut to one uniform clip: the edit is joined from segments whose picture
            # properties differ, and the Shorts step twice sat for over half an hour on it (W46-en, runs
            # cancelled by hand). Every encode here is also time-limited, so a stall costs one Short.
            clip = dest_dir / f"span_{k:02d}.mkv"
            # The voice starts in the pause before the first word, but the picture starts on the story's own
            # first frame, held for that moment: the earlier start showed the tail of the previous shot (W46-en
            # Short 3: a flash of a green tunnel before the source card, founder).
            pre = max(0.0, caption_start - sp.start)
            hold = (f"trim=start={pre:.3f},setpts=PTS-STARTPTS,tpad=start_mode=clone:start_duration={pre:.3f},"
                    if pre > 0.02 else "")
            log.info("Short %d: %s, %.1f–%.1f s", k, sp.title, sp.start, sp.end)
            hook_s = float(cfg.get("post", {}).get("shorts", {}).get("hook_seconds", HOOK_SECONDS))
            over = str(cfg.get("post", {}).get("shorts", {}).get("hook_mode", "card")) == "overlay"
            lead, extra, hook_png = (hook_s if hook_text and not over else 0.0), [], dest_dir / f"hook_{k:02d}.png"
            if hook_text:   # the browser is used here, in order; the encodes below run side by side
                if over:
                    r.still(hook_overlay_html(hook_text, mid_y), hook_png, transparent=True)
                else:
                    r.still(hook_html(hook_text, _show_name(cfg)), hook_png)
                extra = ["-loop", "1", "-i", str(hook_png), "-i", str(chime)]
            over_s = hook_s if hook_text and over else 0.0

            def encode(k=k, sp=sp, span_s=span_s, sub=sub, dest=dest, clip=clip, hold=hold, mid_y=mid_y,
                       title_png=title_png, hook_png=hook_png, hook_text=hook_text, lead=lead, extra=extra,
                       over_s=over_s):
                if not _timed("-ss", f"{sp.start:.3f}", "-t", f"{span_s:.3f}", "-i", str(video),
                              "-vf", f"{hold}scale={SRC_W}:{SRC_H},setsar=1,fps={fps},format=yuv420p", "-af", "aresample=48000",
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-c:a", "pcm_s16le", str(clip)):
                    return None
                try:
                    from pipeline.post import audio as audio_mod
                    voice_gain = min(12.0, -14.0 - audio_mod.measure(clip)["input_i"])
                except Exception:  # noqa: BLE001 — an unmeasurable span falls back to the levelling filter
                    voice_gain = None
                done = _timed("-i", str(clip),
                        "-loop", "1", "-i", str(title_png), "-loop", "1", "-i", str(end_png), *extra,
                        *(["-stream_loop", "-1", "-i", str(bed_wav)] if bed_wav else []),
                        *(["-i", str(outro_file)] if outro_s else []),
                        "-filter_complex", filter_graph(span_s, mid_y, sub, _font(), fps, lead,
                                                        (5 if extra else 3, bed_gain) if bed_wav else None, voice_gain,
                                                        card, ((5 if extra else 3) + (1 if bed_wav else 0), outro_gain) if outro_s else None,
                                                        over_s),
                        "-map", "[v]", "-map", "[a]", "-t", f"{lead + span_s + card:.3f}",
                        # veryfast crf 17 ≈ medium crf 19 in picture quality, at a quarter of the CPU (2026-11-21)
                        "-c:v", "libx264", "-crf", "17", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(fps),
                        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", str(dest))
                for p in (title_png, sub, hook_png, clip):
                    if p:
                        p.unlink(missing_ok=True)
                if not done:
                    dest.unlink(missing_ok=True)
                    return None
                log.info("Short %d written: %s", k, dest.name)
                return dict(asdict(sp), file=dest.name, episode_start=round(to_final(sp.start, sting), 2), hook=hook_text,
                            **({"question": ask} if ask else {}))
            jobs_.append(encode)
        # The Shorts are independent encodes: side by side (2026-11-21; W47-en: 3 × ~65 s one after another).
        from pipeline.post.jobs import run_all, workers
        made += [m for m in run_all(jobs_, min(len(jobs_), workers(cfg))) if m]
        end_png.unlink(missing_ok=True)
        chime.unlink(missing_ok=True)
        if bed_wav:
            bed_wav.unlink(missing_ok=True)
    (dest_dir / "shorts.json").write_text(json.dumps(made, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Shorts: %d made → %s", len(made), dest_dir)
    return made
