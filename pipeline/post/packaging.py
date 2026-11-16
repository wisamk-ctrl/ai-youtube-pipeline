"""
The episode's YouTube package, made in phase post next to the final cut:

- thumbnail.png  (1280×720) — the plan's `thumbnail_text_ar` in big Arabic type, brand palette and
                 fonts, with an optional small still of the presenter at one side. No logos.
- end card       — a 15 s branded card appended to the final video (show name, «اشترك»), with the
                 left of the frame left empty for YouTube's end-screen elements. No captions over it.
- timeline.json  — where every [Section] starts on the FINAL video (after the intro sting is spliced
                 in), the sting and end-card spans and the final duration; phase publish builds the
                 description's chapters from it.

Cards are HTML rendered by the same Chromium the visual cards use (visual_assets.Renderer), with
the brand fonts embedded, so they look the same on every machine.
"""

from __future__ import annotations

import base64
import html
import json
import logging
import subprocess
from pathlib import Path
from typing import Any

from pipeline.post.visual_assets import DISPLAY, FOIL, FOIL_TEXT, GOLD, INK, MONO, NAVY, PAPER, RED, SAND, TEXT, _fonts
from pipeline.script_format import caption_text, extract_cues, spoken_text, spoken_words

log = logging.getLogger(__name__)

THUMB_W, THUMB_H = 1280, 720
YOUTUBE_THUMB_MAX = 2 * 1024 * 1024        # thumbnails().set refuses files over 2 MB


def _show_name(cfg: dict[str, Any]) -> str:
    from pipeline.language import ui
    if cfg.get("language", "ar") != "ar":
        return str(cfg.get("scripting", {}).get(f"channel_name_{cfg['language']}") or ui("show", cfg["language"]))
    return str(cfg.get("scripting", {}).get("channel_name") or ui("show", "ar"))


def _ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


# ── Thumbnail ───────────────────────────────────────────────────────────────
def thumbnail_html(text: str, show: str, face_jpg: bytes | None = None, w: int = THUMB_W, h: int = THUMB_H) -> str:
    """The thumbnail page. `text` is the plan's 2–4 Arabic words; the presenter still (if any) sits
    small at the left, the words fill the right (RTL reading start)."""
    words = text.split()
    size = h * (0.2 if len(words) <= 2 else 0.165)       # 3–4 words still read from a phone grid
    face = ""
    if face_jpg:
        b64 = base64.b64encode(face_jpg).decode()
        face = (f'<div class="face"><img src="data:image/jpeg;base64,{b64}" alt=""></div>')
    text_w = w * (0.64 if face_jpg else 0.86)
    from pipeline.language import ui
    d, align = ui("dir"), ("right" if ui("dir") == "rtl" else "left")
    return f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}
body{{background:{INK};color:{PAPER};font-family:{TEXT}}}
.grid,.glow{{display:none}}
.words{{position:absolute;right:{w * 0.05:.0f}px;top:50%;transform:translateY(-50%);width:{text_w:.0f}px;text-align:{align};
font:800 {size:.0f}px/1.06 {DISPLAY};letter-spacing:-.035em;color:{PAPER};
hyphens:none;word-break:keep-all;overflow-wrap:normal}}
.words b{{{FOIL_TEXT};font-weight:800;padding-right:.05em}}
.bar{{position:absolute;right:{w * 0.05:.0f}px;bottom:{h * 0.09:.0f}px;width:{w * 0.12:.0f}px;height:{h * 0.014:.0f}px;background:{FOIL}}}
.show{{position:absolute;right:{w * 0.05:.0f}px;top:{h * 0.07:.0f}px;font:700 {h * 0.034:.0f}px {MONO};letter-spacing:.12em;text-transform:uppercase;color:{RED}}}
.face{{position:absolute;left:{w * 0.05:.0f}px;top:50%;transform:translateY(-50%);width:{h * 0.42:.0f}px;height:{h * 0.42:.0f}px;
border-radius:50%;overflow:hidden;box-shadow:{h * 0.018:.0f}px {h * 0.018:.0f}px 0 {RED}}}
.face img{{width:100%;height:100%;object-fit:cover}}
</style></head><body><div class="grid"></div><div class="glow"></div>
<div class="show" dir="{d}">{html.escape(show)}</div>{face}
<div class="words" dir="{d}">{_accent_last(words)}</div><div class="bar"></div></body></html>"""


def _accent_last(words: list[str]) -> str:
    """The last word in gold: one accent, so the eye lands on the payoff."""
    if len(words) < 2:
        return html.escape(" ".join(words))
    return html.escape(" ".join(words[:-1])) + f" <b>{html.escape(words[-1])}</b>"


def face_still(video: Path, cfg: dict[str, Any], at: float = 2.0) -> bytes | None:
    """One JPEG of the presenter from the talking head (the face opens the episode): a square crop
    around the face, using the corner-shot crop settings tuned for the current look."""
    if not video.exists():
        return None
    c = cfg.get("visuals", {}).get("corner", {})
    crop, top = float(c.get("face_crop", 0.72)), float(c.get("face_top", 0.0))
    vf = f"crop=ih*{crop}:ih*{crop}:(iw-ih*{crop})/2:ih*{top},scale=480:480"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{at:.2f}", "-i", str(video),
                        "-frames:v", "1", "-vf", vf, "-q:v", "3", "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
                       capture_output=True)
    return r.stdout if r.returncode == 0 and r.stdout else None


def render_thumbnail(out_dir: Path, cfg: dict[str, Any], plan: dict[str, Any] | None = None,
                     talking_head: Path | None = None) -> Path | None:
    """output/<week>/thumbnail.png from the plan's thumbnail_text_ar (never made up when missing)."""
    t = cfg.get("post", {}).get("thumbnail", {})
    if not t.get("enabled", True):
        return None
    if plan is None:
        p = out_dir / "plan.json"
        plan = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    key = f"thumbnail_text_{cfg.get('language', 'ar')}"       # an English week takes the plan's English words
    text = str(plan.get(key) or "").strip()
    if not text:
        log.warning("No %s in plan.json; thumbnail not made", key)
        return None
    face = face_still(talking_head, cfg) if (t.get("face", True) and talking_head) else None
    from pipeline.post.visual_assets import Renderer
    dest = out_dir / "thumbnail.png"
    with Renderer(THUMB_W, THUMB_H) as r:
        r.still(thumbnail_html(text, _show_name(cfg), face), dest)
        if dest.stat().st_size > YOUTUBE_THUMB_MAX:   # a photo can push a PNG past YouTube's limit
            r.page.screenshot(path=str(out_dir / "thumbnail.jpg"), type="jpeg", quality=90)
    log.info("Thumbnail → %s (%s)", dest, "with presenter still" if face else "text only")
    return dest


# ── Opening backdrop ────────────────────────────────────────────────────────
def opening_backdrop_html(show: str, headline: str, line: str, clip_w: int, w: int = 1920, h: int = 1080) -> str:
    """The frame an upright presenter clip sits in (founder 2026-11-13: the casual, natural look is an
    upright clip): the clip fills the far side at full height, this page is everything else — the show's
    name, the episode's two or three words, one line under them. Also the episode's landing frame."""
    from pipeline.language import ui
    rtl = ui("dir") == "rtl"
    near, far = ("right", "left") if rtl else ("left", "right")
    words = headline.split()
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}
body{{background:{INK};color:{PAPER};font-family:{TEXT}}}
.grid{{display:none}}
.edge{{position:absolute;top:0;bottom:0;{far}:{clip_w}px;width:{w * 0.008:.0f}px;background:{RED}}}
.col{{position:absolute;{near}:{w * 0.05:.0f}px;top:{h * 0.1:.0f}px;width:{w - clip_w - w * 0.1:.0f}px;text-align:{near}}}
.show{{display:inline-block;font:700 {h * 0.026:.0f}px {MONO};letter-spacing:.14em;text-transform:uppercase;color:{RED}}}
.words{{font:800 {h * (0.15 if len(words) <= 3 else 0.115):.0f}px/1.02 {DISPLAY};letter-spacing:-.035em;margin-top:{h * 0.05:.0f}px;
hyphens:none;overflow-wrap:normal}}
.words b{{{FOIL_TEXT};padding-right:.05em}}
.line{{font:500 {h * 0.036:.0f}px/1.35 {TEXT};margin-top:{h * 0.04:.0f}px;color:#E4DCF7}}
</style></head><body><div class="grid"></div><div class="edge"></div>
<div class="col" dir="{ui('dir')}"><div class="show">{html.escape(show)}</div>
<div class="words">{_accent_last(words)}</div><div class="line">{html.escape(line)}</div></div></body></html>"""


def opening_backdrop(out_dir: Path, cfg: dict[str, Any], clip_w: int, w: int, h: int) -> Path:
    plan = {}
    if (out_dir / "plan.json").exists():
        plan = json.loads((out_dir / "plan.json").read_text(encoding="utf-8"))
    lang = cfg.get("language", "ar")
    headline = str(plan.get(f"thumbnail_text_{lang}") or _show_name(cfg)).strip()
    line = str(plan.get(f"episode_title_{lang}") or "").strip()
    from pipeline.post.visual_assets import Renderer
    dest = out_dir / "opening_backdrop.png"
    with Renderer(w, h) as r:
        r.still(opening_backdrop_html(_show_name(cfg), headline, line, clip_w, w, h), dest)
    return dest


# ── End card ────────────────────────────────────────────────────────────────
def end_card_html(show: str, w: int = 1920, h: int = 1080) -> str:
    """Show name and «اشترك» in the right column; the left ~55 % stays empty for YouTube's
    end-screen elements (a video tile and the subscribe button are placed there in Studio)."""
    from pipeline.language import ui
    return f"""<!doctype html><html lang="ar"><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}
body{{background:{INK};color:{PAPER};font-family:{TEXT}}}
.grid{{display:none}}
.col{{position:absolute;right:{w * 0.06:.0f}px;top:0;bottom:0;width:{w * 0.36:.0f}px;display:flex;flex-direction:column;
justify-content:center;align-items:flex-start;gap:{h * 0.045:.0f}px;text-align:right}}
.show{{font:800 {h * 0.085:.0f}px/1.05 {DISPLAY};letter-spacing:-.035em}}
.show{{{FOIL_TEXT}}}
.bar{{width:{w * 0.08:.0f}px;height:{h * 0.012:.0f}px;background:{RED}}}
.sub{{font:700 {h * 0.045:.0f}px {TEXT};color:{INK};background:{RED};padding:.3em 1em .36em}}
.note{{font:500 {h * 0.024:.0f}px {MONO};letter-spacing:.1em;text-transform:uppercase;opacity:.75}}
</style></head><body><div class="grid"></div><div class="col" dir="{ui("dir")}">
<div class="show">{html.escape(show)}</div><div class="bar"></div><div class="sub">{ui("subscribe")}</div>
<div class="note">{ui("weekly")}</div></div></body></html>"""


def end_card(cfg: dict[str, Any], out_dir: Path) -> Path | None:
    """The end card as an MP4 with its own soft music (our generated bed, never licensed music),
    sized to the edit; None when post.end_card.enabled is false."""
    e = cfg.get("post", {}).get("end_card", {})
    if not e.get("enabled", True):
        return None
    v = cfg.get("visuals", {})
    w, h, fps = int(v.get("width", 1920)), int(v.get("height", 1080)), int(v.get("fps", 30))
    secs = float(e.get("seconds", 15))
    work = out_dir / "endcard"
    work.mkdir(parents=True, exist_ok=True)
    from pipeline.post.visual_assets import Renderer
    with Renderer(w, h) as r:
        png = r.still(end_card_html(_show_name(cfg), w, h), work / "end_card.png")
    music = str(cfg.get("post", {}).get("audio", {}).get("music", "generated"))
    if music == "none":
        audio_in = ["-f", "lavfi", "-t", f"{secs:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        afilter = "[1:a]anull[a]"
    else:
        from pipeline.post import audio
        bed = audio.music_loop(work / "bed.wav") if music == "generated" else Path(music)
        gain = float(e.get("music_lufs", -20)) - audio.measure(bed)["input_i"]
        audio_in = ["-stream_loop", "-1", "-i", str(bed)]
        afilter = (f"[1:a]atrim=0:{secs:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,"
                   f"volume={gain:.2f}dB,afade=t=in:d=1.5,afade=t=out:st={max(0.0, secs - 3):.3f}:d=3[a]")
    dest = work / "end_card.mp4"
    _ff("-loop", "1", "-framerate", str(fps), "-t", f"{secs:.3f}", "-i", str(png), *audio_in,
        "-filter_complex", f"[0:v]scale={w}:{h},format=yuv420p,setsar=1,fade=t=in:d=0.5[v];{afilter}",
        "-map", "[v]", "-map", "[a]", "-t", f"{secs:.3f}", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-r", str(fps), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(dest))
    return dest


# ── Timeline of the final video ─────────────────────────────────────────────
def section_marks(script: str, srt: Path | None, wpm: int) -> list[tuple[str, float]]:
    """(title, start) of every [Section] on the edit's timeline (before the sting): the start of the
    caption that begins with the section's first spoken words, else the words-per-minute estimate.
    The first section (the cold open) starts at 0."""
    from pipeline.post.overlays import _srt_index
    words = [caption_text(w).strip() for w in spoken_words(spoken_text(script))]
    idx = _srt_index(srt)
    out: list[tuple[str, float]] = []
    for c in extract_cues(script, wpm):
        if c.kind != "section":
            continue
        if c.at_word == 0 or not out:
            out.append((c.text, 0.0))
            continue
        probe = " ".join(words[c.at_word:c.at_word + 3])
        hits = [t for t, text in idx if probe and text.startswith(probe)]
        out.append((c.text, min(hits, key=lambda t: abs(t - c.at_seconds)) if hits else c.at_seconds))
    return out


def to_final(t: float, sting: tuple[float, float] | None) -> float:
    """A time on the edit's timeline → the same moment in the final video (sting = (at, seconds))."""
    if sting and t >= sting[0] - 1e-3:
        return t + sting[1]
    return t


def write_timeline(out_dir: Path, script: str, srt: Path | None, cfg: dict[str, Any],
                   sting: tuple[float, float] | None, end_card_seconds: float | None,
                   final_duration: float | None) -> Path:
    marks = section_marks(script, srt, int(cfg["scripting"]["words_per_minute"]))
    data = {
        "sections": [{"title": t, "start": round(to_final(s, sting), 2)} for t, s in marks],
        "sting": {"at": round(sting[0], 3), "seconds": round(sting[1], 3)} if sting else None,
        "end_card": ({"start": round(final_duration - end_card_seconds, 2), "seconds": end_card_seconds}
                     if end_card_seconds and final_duration else None),
        "duration": round(final_duration, 2) if final_duration else None,
    }
    dest = out_dir / "timeline.json"
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest
