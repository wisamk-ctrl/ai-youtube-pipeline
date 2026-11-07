"""
Visual assets for the shot timeline: every non-face shot becomes an MP4 clip of exactly the
output size and frame rate, a little longer than the shot.

- source  → a news-clipping card (publisher, headline, date): a ~1 s intro (the card lifts in, the
              headline's highlight sweeps, the source line appears), then a drifting push-in
- number  → the figure counting up with an Arabic label, then the same drifting hold
- title   → a short Arabic phrase, large, with the same intro and hold
- stock   → Pixabay (PIXABAY_API_KEY) or Pexels (PEXELS_API_KEY) footage for English search terms,
              animations first, muted and cropped to fill; with no key or no result, a generated
              tech animation (a moving network in the brand colours)

Cards are HTML rendered by Chromium with the brand fonts embedded, so they look the same on
every machine. Any asset that cannot be made returns None and the shot falls back to the
presenter's face (config/visual_standard.md, "Fallbacks").
"""

from __future__ import annotations

import base64
import html
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import requests

from pipeline.models import NewsItem

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
NAVY, GOLD, SAND = "#0B1220", "#E8B24A", "#F4F1EA"


def _font_face(name: str, rel: str) -> str:
    p = ROOT / rel
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f'@font-face{{font-family:{name};src:url(data:font/ttf;base64,{b64}) format("truetype");font-weight:100 900}}'


FONTS = None


def _fonts() -> str:
    global FONTS
    if FONTS is None:
        FONTS = _font_face("Kufi", "lowerthird/fonts/display.ttf") + _font_face("Naskh", "lowerthird/fonts/ui.ttf")
    return FONTS


def _page(body: str, w: int, h: int, extra_css: str = "") -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}
body{{background:radial-gradient(120% 90% at 70% 20%,#16213a 0%,{NAVY} 60%,#070b14 100%);color:{SAND};
font-family:Naskh,Kufi,sans-serif}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(rgba(244,241,234,.035) 1px,transparent 1px),
linear-gradient(90deg,rgba(244,241,234,.035) 1px,transparent 1px);background-size:{w // 24}px {w // 24}px}}
.tag{{position:absolute;top:{h * 0.06:.0f}px;right:{w * 0.05:.0f}px;font:600 {h * 0.026:.0f}px Kufi;color:{GOLD};letter-spacing:.02em}}
{extra_css}</style></head><body><div class="grid"></div><div class="tag">أسبوع الذكاء الاصطناعي</div>{body}</body></html>"""


def source_html(item: NewsItem, w: int, h: int) -> str:
    domain = re.sub(r"^www\.", "", re.sub(r"^https?://([^/]+).*$", r"\1", item.url or ""))
    if "news.google.com" in domain:
        domain = ""
    date = item.published.strftime("%Y-%m-%d") if item.published else ""
    css = f""".clip{{position:absolute;left:50%;top:52%;transform:translate(-50%,-50%) rotate(-1.2deg);
width:{w * 0.66:.0f}px;background:{SAND};color:#14161c;border-radius:{h * 0.012:.0f}px;padding:{h * 0.05:.0f}px {w * 0.04:.0f}px;
box-shadow:0 {h * 0.03:.0f}px {h * 0.08:.0f}px rgba(0,0,0,.55)}}
.pub{{display:inline-block;font:700 {h * 0.03:.0f}px Kufi,sans-serif;background:{NAVY};color:{GOLD};padding:.25em .7em;border-radius:.3em}}
.hl{{font:700 {h * 0.055:.0f}px/1.28 Naskh,Kufi,sans-serif;margin:.55em 0 .5em;hyphens:none;-webkit-hyphens:none;word-break:normal;overflow-wrap:normal}}
.meta{{font:500 {h * 0.024:.0f}px Kufi,sans-serif;color:#5d5a52}}
.credit{{position:absolute;bottom:{h * 0.07:.0f}px;right:{w * 0.05:.0f}px;font:500 {h * 0.026:.0f}px Kufi;color:{SAND};opacity:.75}}"""
    body = f"""<div class="clip"><div class="pub">{html.escape(item.source)}</div>
<div class="hl" dir="auto">{html.escape(item.title.strip())}</div>
<div class="meta" dir="ltr">{html.escape(" · ".join(x for x in (domain, date) if x))}</div></div>
<div class="credit" dir="rtl">المصدر: {html.escape(item.source)}</div>"""
    return _page(body, w, h, css)


def title_html(text: str, w: int, h: int) -> str:
    css = f""".t{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.03:.0f}px}}
.p{{font:700 {h * 0.1:.0f}px/1.3 Kufi,sans-serif;text-align:center;max-width:{w * 0.8:.0f}px}}
.bar{{width:{w * 0.09:.0f}px;height:{h * 0.008:.0f}px;background:{GOLD};border-radius:9px}}"""
    return _page(f'<div class="t"><div class="p" dir="rtl">{html.escape(text)}</div><div class="bar"></div></div>', w, h, css)


NUM_RE = re.compile(r"^(?P<pre>[^\d]*)(?P<num>\d[\d,]*(?:\.\d+)?)(?P<post>.*)$")


def split_figure(fig: str) -> tuple[str, float, str, int, bool] | None:
    """'$1.25T' → ('$', 1.25, 'T', 2 decimals, no commas). None if there is no leading number."""
    m = NUM_RE.match(fig.strip().translate(str.maketrans("٠١٢٣٤٥٦٧٨٩٫٬", "0123456789.,")))
    if not m:
        return None
    raw = m.group("num")
    decimals = len(raw.split(".")[1]) if "." in raw else 0
    return m.group("pre"), float(raw.replace(",", "")), m.group("post"), decimals, "," in raw


def fmt_figure(parts: tuple[str, float, str, int, bool], value: float) -> str:
    pre, _, post, dec, commas = parts
    s = f"{value:,.{dec}f}" if commas else f"{value:.{dec}f}"
    return f"{pre}{s}{post}"


def number_html(figure: str, label: str, w: int, h: int) -> str:
    css = f""".n{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.02:.0f}px}}
#fig{{font:800 {h * 0.22:.0f}px/1 Kufi,sans-serif;color:{GOLD};direction:ltr;font-variant-numeric:tabular-nums}}
.l{{font:600 {h * 0.055:.0f}px/1.35 Naskh,Kufi,sans-serif;max-width:{w * 0.75:.0f}px;text-align:center}}"""
    lab = f'<div class="l" dir="rtl">{html.escape(label)}</div>' if label.strip() else ""
    return _page(f'<div class="n"><div id="fig">{html.escape(figure)}</div>{lab}</div>', w, h, css)


# The cards' ~1 s intro, as CSS animations that end on the still design. Renderer.animate seeks
# them frame by frame (paused, so every frame is deterministic). The highlight sweeps from the
# right, the way the Arabic reads.
INTRO_SECONDS = 1.0
INTRO_CSS = f"""@keyframes fade{{from{{opacity:0}}}}
@keyframes rise{{from{{opacity:0;translate:0 .5em}}}}
@keyframes lift{{from{{opacity:0;translate:0 7%}}}}
@keyframes slide{{from{{opacity:0;translate:1.2em 0}}}}
@keyframes sweep{{from{{background-size:0% .34em}}}}
@keyframes grow{{from{{scale:0 1}}}}
.grid{{animation:fade .5s ease-out both}} .tag{{animation:fade .4s ease-out .1s both}}
.clip{{animation:lift .55s cubic-bezier(.2,.7,.2,1) both}}
.pub{{animation:slide .35s ease-out .25s both}}
.hl,.p{{animation:rise .45s cubic-bezier(.2,.7,.2,1) .12s both}}
.hi{{background:linear-gradient(rgba(232,178,74,.4),rgba(232,178,74,.4)) no-repeat right 0 bottom .1em/100% .34em;
-webkit-box-decoration-break:clone;box-decoration-break:clone;animation:sweep .45s ease-in-out .5s both}}
.meta{{animation:fade .3s ease-out .6s both}} .credit{{animation:rise .35s ease-out .65s both}}
.bar{{animation:grow .5s cubic-bezier(.2,.7,.2,1) .35s both}}
#fig{{animation:fade .3s ease-out both}} .l{{animation:rise .4s ease-out .3s both}}"""
_SEEK_JS = """ms => { document.querySelectorAll('.hl,.p').forEach(e => { if (!e.querySelector('.hi'))
  e.innerHTML = '<span class="hi">' + e.innerHTML + '</span>'; });
  document.getAnimations().forEach(a => { a.pause(); a.currentTime = ms; }); }"""


def animated(page_html: str) -> str:
    return page_html.replace("</style>", INTRO_CSS + "</style>", 1)


class Renderer:
    """One Chromium for all cards of an episode."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        try:
            self.browser = self._pw.chromium.launch()
        except Exception:
            path = os.environ.get("CHROMIUM_PATH") or "/opt/pw-browsers/chromium"
            self.browser = self._pw.chromium.launch(executable_path=path)
        self.page = self.browser.new_page(viewport={"width": self.w, "height": self.h})
        return self

    def __exit__(self, *exc):
        self.browser.close()
        self._pw.stop()

    def still(self, page_html: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        self.page.set_content(page_html, wait_until="load")
        self.page.evaluate("document.fonts.ready")
        self.page.screenshot(path=str(dest))
        return dest

    def animate(self, page_html: str, frames_dir: Path, frames: int, fps: int = 30) -> int:
        """A card's intro (INTRO_CSS) as numbered PNG frames, seeked frame by frame; returns the count."""
        frames_dir.mkdir(parents=True, exist_ok=True)
        self.page.set_content(animated(page_html), wait_until="load")
        self.page.evaluate("document.fonts.ready")
        n = max(1, min(frames, round(INTRO_SECONDS * fps)))
        for k in range(n):
            self.page.evaluate(_SEEK_JS, k * 1000 / fps)
            self.page.screenshot(path=str(frames_dir / f"f{k:04d}.png"))
        return n

    def tech_motion(self, seed: str, frames_dir: Path, seconds: float, fps: int = 30) -> int:
        """A moving network of nodes and travelling pulses, rendered frame by frame (deterministic)."""
        frames_dir.mkdir(parents=True, exist_ok=True)
        self.page.set_content(_page(TECH_MOTION_HTML.format(w=self.w, h=self.h, seed=_seed(seed)), self.w, self.h),
                              wait_until="load")
        n = max(1, round(seconds * fps))
        for k in range(n):
            self.page.evaluate(f"draw({k / fps:.4f})")
            self.page.screenshot(path=str(frames_dir / f"f{k:04d}.png"))
        return n

    def count_up(self, figure: str, label: str, frames_dir: Path, frames: int, fps: int = 30) -> int:
        """Render the count-up (with the card's intro) as numbered PNG frames; returns how many were written."""
        frames_dir.mkdir(parents=True, exist_ok=True)
        # "61% → 84%": the left figure stays, the right one climbs from it. Otherwise from zero.
        left, arrow, right = figure.partition("→") if "→" in figure else ("", "", figure)
        parts = split_figure(right)
        start = (split_figure(left) or (None, 0.0))[1] if arrow else 0.0
        prefix = f"{left.strip()} → " if arrow else ""
        if not parts:
            return self.animate(number_html(figure, label, self.w, self.h), frames_dir, frames, fps)
        self.page.set_content(animated(number_html(figure, label, self.w, self.h)), wait_until="load")
        self.page.evaluate("document.fonts.ready")
        for k in range(frames):
            x = (k + 1) / frames
            ease = 1 - (1 - x) ** 3
            value = start + (parts[1] - start) * ease
            self.page.evaluate("t => document.getElementById('fig').textContent = t", prefix + fmt_figure(parts, value))
            self.page.evaluate(_SEEK_JS, k * 1000 / fps)
            self.page.screenshot(path=str(frames_dir / f"f{k:04d}.png"))
        return frames


def _ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def _enc(fps: int) -> list[str]:
    return ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps)]


def still_clip(png: Path, seconds: float, dest: Path, w: int, h: int, fps: int, push: float = 0.05) -> Path:
    n = max(1, round(seconds * fps))
    vf = (f"scale={w * 2}:{h * 2},zoompan=z='1+{push}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d={n}:s={w}x{h}:fps={fps}")
    _ff("-i", str(png), "-vf", vf, "-frames:v", str(n), *_enc(fps), str(dest))
    return dest


def frames_clip(frames_dir: Path, count: int, seconds: float, dest: Path, w: int, h: int, fps: int) -> Path:
    n = max(1, round(seconds * fps))
    hold = max(0.0, (n - count) / fps)
    _ff("-framerate", str(fps), "-i", str(frames_dir / "f%04d.png"),
        "-vf", f"scale={w}:{h},tpad=stop_mode=clone:stop_duration={hold:.3f}",
        "-frames:v", str(n), *_enc(fps), str(dest))
    return dest


def card_clip(frames_dir: Path, count: int, seconds: float, dest: Path, w: int, h: int, fps: int,
              drift: float = 0.03) -> Path:
    """A card: its intro frames, then the last one held with a slow push-in that also drifts
    sideways (a parallax-like hold instead of a frozen still)."""
    n = max(1, round(seconds * fps))
    m = max(1, n - count)
    p = f"max(0,on-{count})/{m}"
    vf = (f"tpad=stop_mode=clone:stop_duration={m / fps + 1:.3f},scale={w * 2}:{h * 2},"
          f"zoompan=z='1+{drift}*{p}':x='iw/2-(iw/zoom/2)+iw*{drift / 3:.4f}*{p}':y='ih/2-(ih/zoom/2)'"
          f":d=1:s={w}x{h}:fps={fps}")
    _ff("-framerate", str(fps), "-i", str(frames_dir / "f%04d.png"), "-vf", vf, "-frames:v", str(n), *_enc(fps), str(dest))
    return dest


def stock_clip(src: Path, seconds: float, dest: Path, w: int, h: int, fps: int) -> Path:
    n = max(1, round(seconds * fps))
    _ff("-stream_loop", "-1", "-i", str(src),
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},eq=brightness=-0.03:saturation=0.95",
        "-frames:v", str(n), *_enc(fps), str(dest))
    return dest


# ── Stock footage (Pixabay, or Pexels) ───────────────────────────────────────
# Both providers are normalised to one shape: {"id", "duration", "width", "url",
# "user": {"name", "url"}, "video_files": [{"file_type", "width", "height", "link"}]}, with ids
# prefixed by the provider so a cache or a "used" set never mixes them up.
def pick_file(video: dict[str, Any], min_width: int) -> dict[str, Any] | None:
    files = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width") and f.get("link")]
    files = [f for f in files if (f.get("width") or 0) >= (f.get("height") or 0)]  # landscape only
    big = sorted((f for f in files if f["width"] >= min_width), key=lambda f: f["width"])
    return big[0] if big else (max(files, key=lambda f: f["width"]) if files else None)


def pixabay_search(query: str, key: str, per_page: int = 10) -> list[dict[str, Any]]:
    """Animations first (the house look: config/visual_standard.md), then live footage."""
    out: list[dict[str, Any]] = []
    for video_type in ("animation", "film"):
        if len(out) >= 3:
            break
        out += _pixabay(query, key, per_page, video_type)
    return out


def _pixabay(query: str, key: str, per_page: int, video_type: str) -> list[dict[str, Any]]:
    r = requests.get("https://pixabay.com/api/videos/", timeout=30, params={
        "key": key, "q": query[:100], "per_page": max(3, per_page), "safesearch": "true", "video_type": video_type})
    r.raise_for_status()
    out = []
    for h in r.json().get("hits") or []:
        files = [{"file_type": "video/mp4", "width": v.get("width") or 0, "height": v.get("height") or 0, "link": v.get("url")}
                 for v in (h.get("videos") or {}).values() if v.get("url")]
        out.append({"id": f"pixabay_{h['id']}", "duration": h.get("duration", 0), "animation": video_type == "animation",
                    "tags": h.get("tags") or "",
                    "width": max((f["width"] for f in files), default=0), "url": h.get("pageURL"),
                    "user": {"name": h.get("user"), "url": f"https://pixabay.com/users/{h.get('user')}-{h.get('user_id')}/"},
                    "video_files": files})
    return out


def pexels_search(query: str, key: str, per_page: int = 8) -> list[dict[str, Any]]:
    r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key}, timeout=30,
                     params={"query": query, "orientation": "landscape", "per_page": per_page, "size": "medium"})
    r.raise_for_status()
    return [dict(v, id=f"pexels_{v['id']}", tags=" ".join(re.findall(r"[a-z]+", (v.get("url") or "").split("/video/")[-1])))
            for v in r.json().get("videos") or []]


PROVIDERS = {"pixabay": ("PIXABAY_API_KEY", pixabay_search), "pexels": ("PEXELS_API_KEY", pexels_search)}


def stock_search(cfg: dict[str, Any]):
    """(provider name, search(query)) for the first configured provider with a key, else None."""
    order = cfg.get("visuals", {}).get("stock", {}).get("providers", ["pixabay", "pexels"])
    for name in order:
        env, fn = PROVIDERS.get(name, (None, None))
        key = os.environ.get(env or "", "")
        if fn and key:
            return name, (lambda q, fn=fn, key=key: fn(q, key))
    return None


# Off-brand subjects the W45 preview showed (a mermaid, strawberries, a bicycle wheel): a hit tagged
# with any of these is dropped unless the query itself asks for it.
OFF_TOPIC = {
    "mermaid", "fantasy", "fairy", "angel", "unicorn", "dragon", "witch", "magic", "princess",
    "strawberry", "strawberries", "fruit", "fruits", "food", "cake", "coffee", "drink", "cooking", "vegetable",
    "flower", "flowers", "rose", "tree", "trees", "forest", "nature", "garden", "beach", "sea", "ocean",
    "sunset", "landscape", "mountain", "waterfall", "snow", "rain", "grass", "leaf", "leaves",
    "woman", "women", "man", "men", "girl", "boy", "child", "children", "baby", "people", "person", "face",
    "portrait", "couple", "family", "model", "wedding", "love", "heart", "christmas",
    "cat", "dog", "animal", "animals", "bird", "fish", "horse", "butterfly", "insect",
    "bicycle", "bike", "car", "wheel", "sport", "football", "dance", "fashion",
}
_STOP = {"a", "an", "the", "of", "in", "on", "and", "with", "to", "for", "at", "by", "from", "light", "view", "close", "up"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOP and len(w) > 1}


def _stem(w: str) -> str:
    return w[:-1] if len(w) > 3 and w.endswith("s") else w


def relevance(query: str, tags: str) -> int | None:
    """How many of the query's words a hit's tags share; None when the hit must be rejected
    (no shared word, or an off-topic subject the query did not ask for)."""
    q, t = _words(query), _words(tags)
    if (t & OFF_TOPIC) - q:
        return None
    qs, ts = {_stem(w) for w in q}, {_stem(w) for w in t}
    score = len(qs & ts)
    return score if score else None


def fetch_stock(query: str, cache: Path, used: set[str], search, min_width: int, min_seconds: float) -> tuple[Path, dict] | None:
    """Best unused, relevant clip for the query that is long enough; cached on disk by provider id.

    Relevance (tags shared with the query) ranks first, then animation (the house look), then length.
    A hit without tags (a provider that sends none) is kept with the lowest relevance."""
    scored = []
    for v in search(query):
        if v.get("id") in used:
            continue
        r = relevance(query, v["tags"]) if v.get("tags") else 0
        if r is not None:
            scored.append((r, v))
    scored.sort(key=lambda rv: (-rv[0], not rv[1].get("animation", False), rv[1].get("duration", 0) < min_seconds,
                                -(rv[1].get("width") or 0)))
    vids = [v for _, v in scored]
    for v in vids:
        f = pick_file(v, min_width)
        if not f:
            continue
        dest = cache / f"{v['id']}.mp4"
        if not dest.exists():
            from pipeline.video.common import download
            download(f["link"], dest)
        used.add(v["id"])
        user = v.get("user") or {}
        return dest, {"query": query, "id": v["id"], "url": v.get("url"),
                      "author": user.get("name"), "author_url": user.get("url")}
    return None


TECH_MOTION_HTML = """<canvas id="c" width="{w}" height="{h}" style="position:absolute;inset:0"></canvas>
<script>
const W={w}, H={h}; let seed={seed};
const rnd=()=>((seed=(seed*1664525+1013904223)>>>0)/4294967296);
const N=120, nodes=[...Array(N)].map(()=>({{x:rnd()*W,y:rnd()*H,vx:(rnd()-.5)*W*.02,vy:(rnd()-.5)*H*.02,p:rnd()*6.28}}));
const pulses=[...Array(24)].map(()=>({{a:Math.floor(rnd()*N),b:Math.floor(rnd()*N),o:rnd()}}));
const ctx=document.getElementById('c').getContext('2d');
window.draw=(t)=>{{
  ctx.clearRect(0,0,W,H);
  const P=nodes.map(n=>({{x:(n.x+n.vx*t+W*2)%W, y:(n.y+n.vy*t+H*2)%H, p:n.p}}));
  const R=Math.min(W,H)*0.24;
  for(let i=0;i<N;i++) for(let j=i+1;j<N;j++){{
    const dx=P[i].x-P[j].x, dy=P[i].y-P[j].y, d=Math.hypot(dx,dy);
    if(d<R){{ctx.strokeStyle=`rgba(232,178,74,${{0.5*(1-d/R)}})`;ctx.lineWidth=W/1100;ctx.beginPath();ctx.moveTo(P[i].x,P[i].y);ctx.lineTo(P[j].x,P[j].y);ctx.stroke();}}
  }}
  for(const q of P){{const a=.45+.35*Math.sin(t*2+q.p);ctx.fillStyle=`rgba(244,241,234,${{a}})`;ctx.beginPath();ctx.arc(q.x,q.y,W/620,0,6.29);ctx.fill();}}
  for(const u of pulses){{const A=P[u.a],B=P[u.b],k=((t*.35+u.o)%1);
    ctx.fillStyle='rgba(232,178,74,.9)';ctx.beginPath();ctx.arc(A.x+(B.x-A.x)*k,A.y+(B.y-A.y)*k,W/480,0,6.29);ctx.fill();}}
}};
draw(0);
</script>"""


def _seed(text: str) -> int:
    import zlib
    return zlib.crc32(text.encode("utf-8")) or 1


def backdrop_html(seed: str, w: int, h: int) -> str:
    """The no-footage fallback: a branded motion backdrop, varied by the shot's search terms so two
    fallbacks in one episode do not look identical. No text: it never claims to show anything."""
    import random
    rnd = random.Random(seed)
    paths = []
    for _ in range(5):
        y0, y1, y2 = (rnd.uniform(0.15, 0.85) * h for _ in range(3))
        paths.append(f'<path d="M -50 {y0:.0f} C {w * 0.35:.0f} {y1:.0f}, {w * 0.65:.0f} {y2:.0f}, {w + 50} {rnd.uniform(0.2, 0.8) * h:.0f}" '
                     f'stroke="{GOLD}" stroke-opacity="{rnd.uniform(0.12, 0.35):.2f}" stroke-width="{rnd.uniform(1.5, 4):.1f}" fill="none"/>')
    dots = "".join(f'<circle cx="{rnd.uniform(0, w):.0f}" cy="{rnd.uniform(0, h):.0f}" r="{rnd.uniform(1, 3.5):.1f}" '
                   f'fill="{SAND}" fill-opacity="{rnd.uniform(0.15, 0.5):.2f}"/>' for _ in range(70))
    glow = f"radial-gradient(60% 50% at {rnd.uniform(20, 80):.0f}% {rnd.uniform(25, 75):.0f}%,rgba(232,178,74,.16) 0%,transparent 70%)"
    body = f'<div style="position:absolute;inset:0;background:{glow}"></div><svg width="{w}" height="{h}" style="position:absolute;inset:0">{"".join(paths)}{dots}</svg>'
    return _page(body, w, h)


# ── Episode assets ───────────────────────────────────────────────────────────
def build(shots: list, items: list[NewsItem], cfg: dict[str, Any], out_dir: Path) -> tuple[dict[int, Path], list[dict]]:
    """A clip for every non-face shot that can be made; missing ones fall back to the face."""
    v = cfg.get("visuals", {})
    w, h, fps = int(v.get("width", 1920)), int(v.get("height", 1080)), int(v.get("fps", 30))
    work = out_dir / "visuals"
    work.mkdir(parents=True, exist_ok=True)
    by_id = {i.id: i for i in items}
    search = stock_search(cfg)
    used: set[str] = set()
    clips: dict[int, Path] = {}
    credits: list[dict] = []
    stock_src: dict[str, tuple[Path, dict] | None] = {}
    cards_needed = any(s.mode != "face" for s in shots)   # stock needs it too, for the backdrop fallback
    renderer = Renderer(w, h) if cards_needed else None
    if renderer:
        renderer.__enter__()
    try:
        for n, s in enumerate(shots):
            if s.mode == "face":
                continue
            secs = s.seconds + 0.5
            dest = work / f"shot_{n:03d}_{s.kind}.mp4"
            try:
                if s.kind in ("source", "title"):
                    item = by_id.get(s.payload) if s.kind == "source" else None
                    from pipeline.ingestion.publishers import on_screen_ok
                    if s.kind == "title":
                        page = title_html(s.payload, w, h)
                    elif item is not None and not on_screen_ok(item):   # radar note / tier-C outlet: never the credit
                        s.notes.append(f"source {s.payload} ({item.source}) is not creditable on screen; title card instead")
                        page = title_html((item.entities[0] if item.track == "radar" and item.entities else item.title)[:80], w, h)
                    elif item is None:
                        s.notes.append(f"unknown source id {s.payload}; title card instead")
                        page = title_html("المصدر", w, h)
                    else:
                        page = source_html(item, w, h)
                    fdir = work / f"shot_{n:03d}_frames"
                    count = renderer.animate(page, fdir, round(secs * fps), fps)
                    clips[n] = card_clip(fdir, count, secs, dest, w, h, fps)
                elif s.kind == "number":
                    fig, _, label = s.payload.partition("|")
                    fdir = work / f"shot_{n:03d}_frames"
                    count = renderer.count_up(fig.strip(), label.strip(), fdir, min(int(fps * 1.2), round(secs * fps)), fps)
                    clips[n] = card_clip(fdir, count, secs, dest, w, h, fps)
                elif s.kind == "stock":
                    got = None
                    if search:   # fetched per shot: a repeated query gets the next unused clip, not the same one
                        got = fetch_stock(s.payload, work / "stock", used, search[1], w, secs) or stock_src.get(s.payload)
                        if got:
                            stock_src[s.payload] = got
                    if got:
                        clips[n] = stock_clip(got[0], secs, dest, w, h, fps)
                        if got[1] not in credits:
                            credits.append(dict(got[1], provider=search[0]))
                    else:
                        s.notes.append("no stock key" if not search else "no stock result")
                        fdir = work / f"shot_{n:03d}_motion"
                        count = renderer.tech_motion(s.payload, fdir, secs, fps=fps)
                        _ff("-framerate", str(fps), "-i", str(fdir / "f%04d.png"), "-vf", f"scale={w}:{h},fps={fps}",
                            "-frames:v", str(max(1, round(secs * fps))), *_enc(fps), str(dest))
                        clips[n] = dest
            except Exception as exc:  # noqa: BLE001 — one bad asset must not sink the episode
                # Never fall back to the face: its lip sync is why the face is kept to the open and close.
                log.warning("Shot %d (%s %s) failed: %s; tech animation instead", n, s.kind, s.payload[:40], exc)
                s.notes.append(f"asset failed: {exc}")
                try:
                    fdir = work / f"shot_{n:03d}_motion"
                    count = renderer.tech_motion(s.payload or str(n), fdir, secs, fps=fps)
                    _ff("-framerate", str(fps), "-i", str(fdir / "f%04d.png"), "-vf", f"scale={w}:{h},fps={fps}",
                        "-frames:v", str(max(1, round(secs * fps))), *_enc(fps), str(dest))
                    clips[n] = dest
                except Exception as exc2:  # noqa: BLE001
                    log.warning("Shot %d fallback animation failed too: %s; face instead", n, exc2)
    finally:
        if renderer:
            renderer.__exit__(None, None, None)
    (out_dir / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Visuals: %d clips made, %d shots fell back to the face, %d stock credits",
             len(clips), sum(1 for k, s in enumerate(shots) if s.mode != "face" and k not in clips), len(credits))
    return clips, credits
