"""Phone-friendly HTML of a HeyGen paste pack, one copy button per scene.

Usage: python scripts/paste_pack_html.py <heygen_paste.md> <out.html> <week label>
"""
import re, html, sys
md, out, week = sys.argv[1], sys.argv[2], sys.argv[3]
p=open(md,encoding='utf-8').read()
scenes=re.findall(r'## Scene (\d+)\n\n```\n(.*?)\n```', p, re.S)
mins=re.search(r'about ([\d.]+) minutes', p).group(1)
cards=''.join(f'''<section class="scene"><div class="bar"><h2>Scene {n}</h2><span class="meta">{len(t.split())} words</span>
<button onclick="cp(this)">Copy</button></div><div class="text" dir="rtl" lang="ar">{html.escape(t.strip())}</div></section>''' for n,t in scenes)
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>HeyGen Paste Pack</title><style>
:root{{--bg:#f7f4ee;--card:#fff;--fg:#1c1b19;--muted:#6d665a;--accent:#9a6a1c;--line:#e4ddd0}}
@media (prefers-color-scheme:dark){{:root{{--bg:#13120f;--card:#1d1b17;--fg:#eee8dc;--muted:#a69e8f;--accent:#e2b25e;--line:#2e2a24}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;padding:20px 16px 60px;max-width:760px;margin-inline:auto}}
h1{{font-size:22px;margin:0 0 6px}} .sub{{color:var(--muted);margin:0 0 14px}}
ol{{padding-inline-start:20px;color:var(--muted);margin:0 0 20px}} li{{margin-bottom:4px}}
.scene{{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:0 0 16px;overflow:hidden}}
.bar{{display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:1px solid var(--line)}}
.bar h2{{font-size:16px;margin:0;color:var(--accent)}} .meta{{color:var(--muted);font-size:13px;flex:1}}
button{{font:600 14px system-ui;padding:8px 16px;border-radius:8px;border:0;background:var(--accent);color:#fff;cursor:pointer}}
button.ok{{background:#2e7d32}}
.text{{padding:14px 16px;font:21px/1.9 "Noto Naskh Arabic","Geeza Pro",system-ui,sans-serif;white-space:pre-wrap;word-break:break-word}}
</style></head><body>
<h1>HeyGen paste pack · {week}</h1>
<p class="sub">{len(scenes)} scenes, about {mins} minutes. Avatar “Sam -- 1”, your Jordanian voice clone. The “...” marks are pauses; keep them.</p>
<ol><li>In HeyGen, start a new video with your avatar and voice.</li>
<li>Make one scene per block below and paste each block into its scene, in order.</li>
<li>Render (4K if your plan allows, otherwise 1080p).</li>
<li>Send me the video’s ID or share link. I’ll import it and add the cue cards and subtitles.</li></ol>
{cards}
<script>
function cp(b){{const t=b.closest('.scene').querySelector('.text').innerText;
 const done=()=>{{b.textContent='Copied';b.classList.add('ok');setTimeout(()=>{{b.textContent='Copy';b.classList.remove('ok')}},1500)}};
 if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(t).then(done,()=>fb(t,done))}}else fb(t,done)}}
function fb(t,done){{const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();
 try{{document.execCommand('copy');done()}}catch(e){{}}a.remove()}}
</script></body></html>'''
open(out,'w',encoding='utf-8').write(page)
print(len(scenes),'scenes', [len(t) for _,t in scenes])
