"""Channel banner (2560x1440, text inside YouTube's 1546x423 safe area) and logo (800x800).

    python scripts/brand_assets.py assets/brand
"""
import sys
sys.path.insert(0, '.')
from pathlib import Path
from pipeline.post.visual_assets import _fonts, Renderer, NAVY, SAND, GOLD
out = Path(sys.argv[1])
grid = ("background-image:linear-gradient(rgba(244,241,234,.045) 1px,transparent 1px),"
        "linear-gradient(90deg,rgba(244,241,234,.045) 1px,transparent 1px);")
bars = "".join(f'<div style="width:{w}px;height:{h}px;background:{c};border-radius:6px"></div>'
               for w, h, c in ((26, 60, "#5C6B86"), (26, 82, "#5C6B86"), (26, 104, "#5C6B86"), (26, 126, "#5C6B86"),
                               (26, 148, "#5C6B86"), (26, 170, "#5C6B86"), (26, 214, GOLD)))
banner = f"""<!doctype html><html><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:2560px;height:1440px;overflow:hidden}}
body{{background:radial-gradient(70% 70% at 50% 50%,#1b2a4a 0%,{NAVY} 60%,#060a12 100%);color:{SAND};font-family:Kufi,sans-serif}}
.g{{position:absolute;inset:0;{grid}background-size:64px 64px}}
.safe{{position:absolute;left:507px;top:508px;width:1546px;height:423px;display:flex;align-items:center;gap:70px}}
.bars{{display:flex;align-items:flex-end;gap:14px;height:230px}}
.t{{font:800 132px/1 Kufi;letter-spacing:-.01em}} .t b{{color:{GOLD}}}
.u{{height:10px;background:{GOLD};border-radius:9px;margin:22px 0 26px;width:100%}}
.s{{font:600 44px/1.3 Kufi;opacity:.9}}
</style></head><body><div class="g"></div><div class="safe"><div class="bars">{bars}</div>
<div><div class="t">This Week in <b>AI</b></div><div class="u"></div>
<div class="s">The AI news that matters for the Gulf<br>Every Sunday · with Wissam</div></div></div></body></html>"""
logo = f"""<!doctype html><html><head><meta charset="utf-8"><style>{_fonts()}
html,body{{margin:0;width:800px;height:800px;overflow:hidden}}
body{{background:radial-gradient(80% 80% at 35% 30%,#1f3157 0%,{NAVY} 65%,#060a12 100%);display:grid;place-items:center;font-family:Kufi}}
.w{{display:flex;flex-direction:column;align-items:center;gap:26px}}
.bars{{display:flex;align-items:flex-end;gap:16px;height:250px}}
.bars div{{width:46px;border-radius:9px}}
.t{{font:800 120px/1 Kufi;color:{SAND}}} .t b{{color:{GOLD}}}
</style></head><body><div class="w"><div class="bars">
{''.join(f'<div style="height:{h}px;background:{c}"></div>' for h, c in ((90, "#5C6B86"), (130, "#5C6B86"), (170, "#5C6B86"), (250, GOLD)))}
</div><div class="t">TW<b>AI</b></div></div></body></html>"""
with Renderer(2560, 1440) as r:
    r.still(banner, out / "banner.png")
with Renderer(800, 800) as r:
    r.still(logo, out / "logo.png")
