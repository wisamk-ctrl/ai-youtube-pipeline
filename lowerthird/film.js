// Reusable lower-third for «أسبوع الذكاء الاصطناعي». Pure function of time on a TRANSPARENT canvas,
// so scripts/render_alpha.mjs can export it as a PNG sequence → ProRes 4444 / VP9 with alpha and the
// editor overlays it on the talking-head video wherever the presenter is framed.
//
// Content comes from the URL so one film serves every guest/topic:
//   lowerthird/index.html?name=وسام&title=أسبوع الذكاء الاصطناعي&dur=6
// Timeline (seconds): 0-0.7 in · hold · last 0.6 s out. Bottom-RIGHT anchored (RTL reading start).

const params = new URLSearchParams(location.search);
const NAME = params.get('name') || 'وسام';
const TITLE = params.get('title') || 'أسبوع الذكاء الاصطناعي';
const DUR = Number(params.get('dur') || 6);
if (params.get('preview') === '1') document.body.classList.add('preview');

const C = { navy: '#0B1220', paper: '#F4F1EA', accent: '#E9B44C', muted: '#5C6B86' };
const W = 1920, H = 1080, SAFE = 96;          // 5% title-safe margin
const canvas = document.getElementById('film');
const ctx = canvas.getContext('2d', { alpha: true });

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const prog = (t, a, b) => clamp((t - a) / (b - a));
const outQuint = (x) => 1 - Math.pow(1 - x, 5);
const inQuart = (x) => x * x * x * x;
// closed-form under-damped spring (settles ~0.6 s), pure function of time
const spring = (t, zeta = 0.68, w = 14) => (t <= 0 ? 0 : 1 - Math.exp(-zeta * w * t) * (Math.cos(w * Math.sqrt(1 - zeta * zeta) * t) + (zeta / Math.sqrt(1 - zeta * zeta)) * Math.sin(w * Math.sqrt(1 - zeta * zeta) * t)));

function rtl(str, x, y, f, color, alpha = 1) {
  ctx.save(); ctx.globalAlpha = alpha; ctx.font = f; ctx.fillStyle = color;
  ctx.textAlign = 'right'; ctx.direction = 'rtl'; ctx.textBaseline = 'alphabetic';
  ctx.fillText(str, x, y); ctx.restore();
}
function measure(str, f) { ctx.font = f; return ctx.measureText(str).width; }

function draw(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const fName = '700 72px Display', fTitle = '500 44px UI';
  const nameW = measure(NAME, fName), titleW = measure(TITLE, fTitle);
  const padX = 36, barW = 10, gap = 26;
  const panelW = Math.max(nameW, titleW) + padX * 2;
  const panelH = 150;
  const right = W - SAFE, bottom = H - SAFE;
  const x0 = right - barW - gap - panelW;             // panel's left edge
  const y0 = bottom - panelH;

  // in: bar grows up from the baseline, panel wipes right→left from the bar, text follows
  const kIn = spring(t - 0.05);
  const barH = panelH * clamp(outQuint(prog(t, 0, 0.35)));
  const wipe = clamp(spring(t - 0.18));
  // out: everything slides right behind the frame edge and fades (last 0.6 s)
  const out = inQuart(prog(t, DUR - 0.6, DUR));
  const dx = out * (panelW + barW + gap + SAFE + 40);
  ctx.save();
  ctx.translate(dx, 0);
  ctx.globalAlpha = 1 - out * 0.4;

  // gold bar (RTL anchor on the right)
  ctx.fillStyle = C.accent;
  ctx.fillRect(right - barW, bottom - barH, barW, barH);

  // panel: navy at 92%, revealed from its right edge toward the left
  const pw = panelW * wipe;
  ctx.save();
  ctx.beginPath(); ctx.rect(x0 + panelW - pw, y0, pw, panelH); ctx.clip();
  ctx.fillStyle = 'rgba(11,18,32,0.92)';
  ctx.beginPath(); ctx.roundRect(x0, y0, panelW, panelH, [12, 0, 0, 12]); ctx.fill();
  // thin paper rule between the two lines
  ctx.fillStyle = 'rgba(244,241,234,0.18)';
  ctx.fillRect(x0 + padX, y0 + 88, panelW - padX * 2, 2);
  // name (display face) and title (UI face), each sliding in from the right as the wipe passes
  const slide = (1 - kIn) * 60;
  rtl(NAME, x0 + panelW - padX + slide, y0 + 70, fName, C.paper, clamp(kIn * 1.4));
  rtl(TITLE, x0 + panelW - padX + slide * 1.3, y0 + 130, fTitle, C.accent, clamp((kIn - 0.15) * 1.4));
  ctx.restore();
  ctx.restore();
}

window.seek = (t) => draw(t);
window.DURATION = DUR;
try { await Promise.all([document.fonts.load('700 72px Display'), document.fonts.load('500 44px UI')]); }
catch (e) { console.error('font load failed:', e.message); }
window.filmReady = true;
draw(0);
if (params.get('render') !== '1') {          // preview loop in a browser
  const t0 = performance.now();
  (function loop() { draw(((performance.now() - t0) / 1000) % DUR); requestAnimationFrame(loop); })();
}
