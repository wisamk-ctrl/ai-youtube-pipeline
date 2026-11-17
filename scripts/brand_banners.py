import sys, base64, math, random
sys.path.insert(0, '/home/user/ai-youtube-pipeline')
from pathlib import Path
import playwright.sync_api as ps
_l = ps.BrowserType.launch
ps.BrowserType.launch = lambda self, **k: _l(self, executable_path='/opt/pw-browsers/chromium', **k)
from pipeline.post.visual_assets import DISPLAY, FOIL, FOIL_TEXT, INK, MONO, PAPER, TEXT, Renderer, _fonts
out = Path(sys.argv[1])
face = base64.b64encode(Path(sys.argv[2]).read_bytes()).decode()
G = "#D9B13B"

def ring(d):
    """The emblem's circuit rays around a circle of diameter d (same drawing as the logo)."""
    rnd = random.Random(7); c = d * 0.8; S = c * 2; out_ = []
    for k in range(30):
        a = 2 * math.pi * k / 30 + rnd.uniform(-0.05, 0.05)
        r0, r1 = d * 0.545, d * rnd.uniform(0.62, 0.76)
        x0, y0, x1, y1 = c + r0 * math.cos(a), c + r0 * math.sin(a), c + r1 * math.cos(a), c + r1 * math.sin(a)
        op = rnd.uniform(0.45, 0.95); w = d * 0.006; dot = d * 0.013
        if rnd.random() < 0.45:
            b = a + rnd.choice((-1, 1)) * math.pi / 2; L = d * rnd.uniform(0.055, 0.14)
            x2, y2 = x1 + L * math.cos(b), y1 + L * math.sin(b)
            out_.append(f'<polyline points="{x0:.1f},{y0:.1f} {x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f}" fill="none" stroke="{G}" stroke-width="{w:.1f}" stroke-opacity="{op:.2f}" stroke-linejoin="round"/>'
                        f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="{dot:.1f}" fill="{INK}" stroke="{G}" stroke-width="{w:.1f}" stroke-opacity="{op:.2f}"/>')
        else:
            out_.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{G}" stroke-width="{w:.1f}" stroke-opacity="{op:.2f}"/>'
                        f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="{dot:.1f}" fill="{G}" fill-opacity="{op:.2f}"/>')
    return S, f'<svg width="{S:.0f}" height="{S:.0f}" style="position:absolute;left:{-(S - d) / 2:.0f}px;top:{-(S - d) / 2:.0f}px">{"".join(out_)}</svg>'

def page(w, h, left, top, size, wrap, d, px, py, glow):
    S, svg = ring(d)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}
body{{background:radial-gradient({glow} at {px + d / 2:.0f}px {py + d / 2:.0f}px,#43209A 0%,{INK} 60%,#1E0A47 100%);color:{PAPER};font-family:{TEXT}}}
.s{{position:absolute;left:{left}px;top:{top}px}}
.t{{font:800 {size}px/1 {DISPLAY};letter-spacing:-.045em;white-space:nowrap}} .g{{{FOIL_TEXT};padding-right:.04em}}
.r{{width:{size * 1.1:.0f}px;height:{size * 0.07:.0f}px;background:{FOIL};margin:{size * 0.2:.0f}px 0}}
.l{{font:500 {size * 0.3:.0f}px/1.28 {TEXT};max-width:{wrap}px}}
.h{{font:600 {size * 0.165:.0f}px/1 {MONO};letter-spacing:.14em;text-transform:uppercase;color:#E8CD7C;margin-top:{size * 0.2:.0f}px}}
.p{{position:absolute;left:{px}px;top:{py}px;width:{d}px;height:{d}px}}
.f{{position:absolute;inset:0;border-radius:50%;background:url(data:image/png;base64,{face}) 50% 16%/215% auto no-repeat;
box-shadow:0 0 0 {d * 0.022:.1f}px {G},0 0 {d * 0.25:.0f}px rgba(217,177,59,.25)}}
</style></head><body><div class="s"><div class="t"><span class="g">AI</span> This Week</div><div class="r"></div>
<div class="l">What changed in AI, and what it means for business.</div><div class="h">With Wissam Kishek</div></div>
<div class="p">{svg}<div class="f"></div></div></body></html>"""
with Renderer(2560, 1440) as r:   # everything inside the 1546×423 centre that every device shows
    r.still(page(2560, 1440, 540, 560, 132, 600, 372, 1610, 534, "900px 700px"), out / "youtube_banner_2560x1440.png")
with Renderer(2256, 382) as r:
    r.still(page(2256, 382, 300, 62, 100, 900, 290, 1690, 46, "700px 500px"), out / "linkedin_banner_2256x382.png")
