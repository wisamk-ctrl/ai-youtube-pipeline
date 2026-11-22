import re,sys,html,pathlib
S=sys.argv[1]; extra=sys.argv[2:]   # extra = new colloquial files (parts written later)
srcs=['reviewed/2026-W47/script.md','lab/voice_training/w46_ar_script.md','reviewed/2026-W43-jo/script.md',
      'lab/ar_training_2.md','lab/ar_training_3.md','lab/ar_mix_w45_part1.txt']+extra
paras=[]
for p in srcs:
    t=pathlib.Path(p).read_text(encoding='utf-8')
    for block in re.split(r'\n\s*\n',t):
        lines=[l.strip() for l in block.split('\n') if l.strip() and not l.strip().startswith(('[','#','<'))]
        txt=re.sub(r'\{[^}]*\}','',' '.join(lines)); txt=re.sub(r'\*\*|__|`','',txt).strip()
        if len(txt.split())>=3 and re.search(r'[؀-ۿ]',txt): paras.append(txt)
per=125*30; parts=[[]]; n=0
for p in paras:
    if n+len(p.split())>per and parts[-1]: parts.append([]); n=0
    parts[-1].append(p); n+=len(p.split())
css="""body{background:#fbf8f1;color:#1d1a2e;font-family:'Noto Naskh Arabic','Geeza Pro','Segoe UI',sans-serif;max-width:900px;margin:0 auto;padding:24px 20px 80px;line-height:2.1}
h1{font-size:28px} h2{font-size:24px;margin-top:56px;border-bottom:2px solid #c79a35;padding-bottom:6px}
p{font-size:27px;margin:0 0 26px} .n{color:#b8892b;font-size:15px;margin-left:10px;font-family:monospace}
.tip{font-size:19px;background:#fff;border-right:4px solid #c79a35;padding:12px 16px}"""
total=sum(len(p.split()) for p in paras)
out=[f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>تدريب الصوت</title><style>{css}</style></head><body>',
 f'<h1>نص تدريب الصوت — حوالي {round(total/125)} دقيقة</h1>',
 '<p class="tip">اقرأ بنفس طريقة الحلقة: هادي، واضح، باللهجة. سجّل كل قسم بملف لحاله (حوالي ٣٠ دقيقة). نفس المايك، نفس المسافة، نفس الغرفة. إذا غلطت، وقّف ثانيتين وأعد الجملة كاملة.</p>']
k=0
for i,part in enumerate(parts,1):
    w=sum(len(p.split()) for p in part); out.append(f'<h2>القسم {i} — حوالي {round(w/125)} دقيقة</h2>')
    for p in part:
        k+=1; out.append(f'<p><span class="n">{k}</span>{html.escape(p)}</p>')
out.append('</body></html>')
pathlib.Path('lab/voice_training_long_rtl.html').write_text('\n'.join(out),encoding='utf-8')
print('words',total,'minutes',round(total/125),'parts',[sum(len(p.split()) for p in pt) for pt in parts])
