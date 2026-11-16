"""The channel's brand files (config/brand.md): logo 800x800, YouTube banner 2560x1440 (text inside
the 1546x423 area every device shows) and the LinkedIn page banner 2256x382.

    python scripts/brand_assets.py assets/brand
"""
import sys
sys.path.insert(0, '.')
from pathlib import Path

from pipeline.post.visual_assets import DISPLAY, FOIL, FOIL_TEXT, INK, MONO, PAPER, STONE, TEXT, Renderer, _fonts

out = Path(sys.argv[1])
LINE = "What changed in AI, and what it means for business."
HOST = "With Wissam Kishek"


def page(w: int, h: int, css: str, body: str) -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{_fonts()}'
            f'html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden}}body{{background:{INK};color:{PAPER};font-family:{TEXT}}}'
            f'.g{{{FOIL_TEXT};padding-right:.04em}}{css}</style></head><body>{body}</body></html>')


logo = page(800, 800, f""".w{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:0 110px}}
.a{{font:800 300px/.9 {DISPLAY};letter-spacing:-.06em}} .b{{font:700 92px/1 {DISPLAY};letter-spacing:-.04em;margin-top:26px}}
.r{{width:150px;height:14px;background:{FOIL};margin-top:44px}}""",
            '<div class="w"><div class="a"><span class="g">AI</span></div><div class="b">This Week</div><div class="r"></div></div>')


def banner(w: int, h: int, left: int, top: int, size: int) -> str:
    return page(w, h, f""".s{{position:absolute;left:{left}px;top:{top}px}}
.t{{font:800 {size}px/1 {DISPLAY};letter-spacing:-.045em}} .r{{width:{size * 1.1:.0f}px;height:{size * 0.07:.0f}px;background:{FOIL};margin:{size * 0.22:.0f}px 0}}
.l{{font:500 {size * 0.3:.0f}px/1.3 {TEXT}}} .h{{font:600 {size * 0.17:.0f}px/1 {MONO};letter-spacing:.14em;text-transform:uppercase;color:{STONE};margin-top:{size * 0.2:.0f}px}}""",
                f'<div class="s"><div class="t"><span class="g">AI</span> This Week</div><div class="r"></div>'
                f'<div class="l">{LINE}</div><div class="h">{HOST}</div></div>')


for name, w, h, html in (("logo_800.png", 800, 800, logo),
                         ("youtube_banner_2560x1440.png", 2560, 1440, banner(2560, 1440, 560, 548, 150)),
                         ("linkedin_banner_2256x382.png", 2256, 382, banner(2256, 382, 620, 62, 110))):
    with Renderer(w, h) as r:
        r.still(html, out / name)
