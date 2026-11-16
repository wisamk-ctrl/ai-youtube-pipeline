// أسبوع الذكاء الاصطناعي — intro sting. Pure function of time: window.seek(t) paints frame t.
// Timing in beats (u) on the 128 bpm grid in beats.json; docs/shotlist.md is the plan.
import * as M from './lib/motion.js';

const { W, H, FORMAT, E, prog, lerp, clamp, springU, springKeys, SPRING, wobble, font, fill, rrect } = M;

// assets/brand.json — one accent.
const C = { navy: '#2C0F66', paper: '#FFFFFF', accent: '#D9B13B', muted: '#6B52A8' };   // config/brand.md
const LATIN = new URLSearchParams(location.search).get('lang') === 'en';
const DISPLAY = LATIN ? 'DisplayEN' : 'Display', UI = LATIN ? 'UIEN' : 'UI';
// ?lang=en renders the English sting (assets/intro_sting_en.mp4): same film, read left to right.
const EN = new URLSearchParams(location.search).get('lang') === 'en';
const TITLE = EN ? ['AI', 'This', 'Week'] : ['أسبوع', 'الذكاء', 'الاصطناعي'];   // reading order
const TAGLINE = EN ? 'The weekly briefing for business and tech leaders' : 'نشرة أسبوعية لقادة الأعمال والتقنية';
const PRESENTER = EN ? 'with Wissam' : 'مع وسام';

// [beat, label, sfx, opts] — sfx.mjs voices every one of these.
const HITS = [
  [0, 'signal line sweeps', 'whoosh', { len: 0.5, from: 400, to: 3200 }],
  [0.5, 'word 1 lands', 'thud'],
  [1.5, 'word 2 slides in', 'pop', { pitch: 'A4' }],
  [2.5, 'word 3 slides in (gold)', 'pop', { pitch: 'D5' }],
  [4, 'title lifts, week bars', 'impact'],
  [4.5, 'bar 2', 'click', { gain: 2 }], [5, 'bar 3', 'click', { gain: 2 }], [5.5, 'bar 4', 'click', { gain: 2 }],
  [6, 'bar 5', 'click', { gain: 2 }], [6.5, 'bar 6', 'click', { gain: 2 }],
  [7, 'bar 7 (today) lights up', 'bell', { pitch: 'D6' }],
  [5.5, 'tagline types on', 'type', { n: 18, len: 0.9 }],
  [7.5, 'bars fold into underline', 'sub', { len: 0.6 }],
  [8, 'presenter name', 'bell', { pitch: 'A5' }],
];

// ---------------------------------------------------------------- RTL word layout
// Canvas shapes a whole Arabic word correctly; we only ever position whole words, from the right.
const wcache = new Map();
function widths(ctx, words, f) {
  const key = f + '|' + words.join('|');
  if (!wcache.has(key)) {
    ctx.font = f;
    const ws = words.map((w) => ctx.measureText(w).width);
    wcache.set(key, { ws, total: ws.reduce((a, b) => a + b, 0) });
  }
  return wcache.get(key);
}
// Right edge x of word i when the whole line is right-aligned at `right` with `gap` between words.
const wordRight = (ws, i, right, gap) => right - ws.slice(0, i).reduce((a, b) => a + b, 0) - gap * i;
function word(ctx, str, x, y, f, color, { sx = 1, sy = 1, alpha = 1, left = false } = {}) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(x, y); ctx.scale(sx, sy);
  ctx.font = f; ctx.fillStyle = color; ctx.textAlign = left ? 'left' : 'right'; ctx.direction = EN ? 'ltr' : 'rtl';
  ctx.fillText(str, 0, 0);
  ctx.restore();
}

// ---------------------------------------------------------------- title lockup geometry
const SIZE = 168, GAP = 0.22 * SIZE;
function lockup(ctx, f) {
  const { ws, total } = widths(ctx, TITLE, f);
  return { ws, total: total + GAP * (TITLE.length - 1) };
}

// Lockup transform over the film: centre y and scale, as spring keys so moves overlap cleanly.
function lockupPose(u) {
  const [cy, s] = springKeys(u, [
    [0, [H * 0.52, 1]],
    [4, [H * 0.30, 0.72]],
    [7.5, [H * 0.50, 0.85]],
  ], SPRING.gentle);
  return { cy, s };
}

// ---------------------------------------------------------------- draw
// The backdrop (config/brand.md): a soft violet glow, a gold ring that draws itself, circuit rays that
// grow out of it with a node on each tip, and slow gold motes drifting outward. All a function of u.
const rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
function backdrop(ctx, u) {
  const cx = W / 2, cy = H / 2, R = H * 0.41;
  const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, H * 0.95);
  g.addColorStop(0, '#45219E'); g.addColorStop(0.55, C.navy); g.addColorStop(1, '#1E0A47');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save();
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const ring = E.outQuint(prog(u, 0, 2.4));
  ctx.strokeStyle = C.accent; ctx.globalAlpha = 0.5; ctx.lineWidth = 7;
  ctx.beginPath(); ctx.arc(cx, cy, R, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * ring); ctx.stroke();
  const N = 34, turn = u * 0.012;
  for (let k = 0; k < N; k++) {
    const a = (Math.PI * 2 * k) / N + (rnd(k) - 0.5) * 0.1 + turn - Math.PI / 2;
    const start = 0.5 + (k / N) * 2.2;                       // follows the ring round
    const grow = E.outQuint(prog(u, start, start + 1.1));
    if (grow <= 0) continue;
    const r0 = R + 26, r1 = r0 + (70 + rnd(k + 50) * 150) * grow;
    const x0 = cx + r0 * Math.cos(a), y0 = cy + r0 * Math.sin(a), x1 = cx + r1 * Math.cos(a), y1 = cy + r1 * Math.sin(a);
    const pulse = 0.5 + 0.5 * Math.sin(u * 1.3 + k * 1.7);
    ctx.globalAlpha = (0.3 + 0.45 * rnd(k + 9)) * (0.7 + 0.3 * pulse);
    ctx.lineWidth = 3.5; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1);
    let tx = x1, ty = y1;
    if (rnd(k + 20) < 0.45) {                                // an elbow, like a circuit trace
      const b = a + (rnd(k + 30) < 0.5 ? -1 : 1) * Math.PI / 2, len = (30 + rnd(k + 40) * 50) * clamp(grow * 1.6 - 0.6);
      tx = x1 + len * Math.cos(b); ty = y1 + len * Math.sin(b); ctx.lineTo(tx, ty);
    }
    ctx.stroke();
    const pop = clamp(grow * 2 - 1);
    if (pop > 0) { ctx.fillStyle = C.accent; ctx.beginPath(); ctx.arc(tx, ty, 8 * pop * (0.85 + 0.3 * pulse), 0, Math.PI * 2); ctx.fill(); }
  }
  for (let k = 0; k < 70; k++) {                             // motes drifting outward
    const a = rnd(k + 100) * Math.PI * 2, life = (rnd(k + 200) + u * (0.035 + 0.03 * rnd(k + 300))) % 1;
    const r = R * 0.9 + life * H * 0.75;
    ctx.globalAlpha = Math.sin(life * Math.PI) * 0.55 * clamp(u / 1.5);
    ctx.fillStyle = k % 5 ? C.accent : C.paper;
    ctx.beginPath(); ctx.arc(cx + r * Math.cos(a), cy + r * Math.sin(a), 2 + 3 * rnd(k + 400), 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}

function draw(ctx, u) {
  backdrop(ctx, u);
  const safe = FORMAT.safe;
  const f = font(SIZE, 800, DISPLAY);
  const L = lockup(ctx, f);
  const { cy, s } = lockupPose(u);
  // Unscaled lockup geometry (scale 1, centred on W/2, cy); the words are drawn inside a
  // zoomAbout(s) so the lift/scale pose reads as one object. Scaled copies for the underline.
  const right0 = W / 2 + L.total / 2, lineY0 = cy + SIZE * 0.42;
  const lineY = cy + SIZE * 0.42 * s, lineR = W / 2 + (L.total / 2) * s, lineL = W / 2 - (L.total / 2) * s;

  // --- signal line (u 0..1): head races right→left and leaves the underline behind it
  const sweep = E.outQuint(prog(u, -0.45, 0.9));   // already 35% across on frame 0
  const headX = lerp(W + 60, lineL, sweep);
  if (u < 7.5) {
    ctx.fillStyle = C.accent;
    ctx.fillRect(headX, lineY - 2, Math.max(0, lineR - headX), 4);
    if (u < 1.2) {                                     // bright head with a short tail
      const tail = 420 * (1 - sweep) + 60;
      const g = ctx.createLinearGradient(headX, 0, headX + tail, 0);
      g.addColorStop(0, C.paper); g.addColorStop(1, 'rgba(233,180,76,0)');
      ctx.fillStyle = g; ctx.fillRect(headX, lineY - 9, tail, 18);
    }
  }

  // --- title words, right to left. Word 1 drops from above; words 2-3 arrive from the LEFT
  // (their final slot is left of the previous word, so they never cross it).
  const starts = [0.5, 1.5, 2.5];
  ctx.save(); M.zoomAbout(ctx, s, W / 2, cy);
  TITLE.forEach((w, i) => {
    const k = springU(u, starts[i], SPRING.bouncy);
    if (k <= 0) return;
    // English mirrors the line: word i's right edge counted from the left, later words arrive from the right.
    const xr = EN ? W - wordRight(L.ws, i, right0, GAP) + L.ws[i] : wordRight(L.ws, i, right0, GAP);
    let x = xr, y = lineY0, sx = 1, sy = 1;
    if (i === 0) { y = lineY0 - (1 - k) * 220; const q = 0.05 * wobble((u - 0.5) * 0.469, 2.6, 7); sx = 1 + q; sy = 1 - q; }
    else x = xr + (EN ? 1 : -1) * (1 - Math.min(k, 1)) * 360;
    word(ctx, w, x, y, f, i === (EN ? 0 : 2) ? C.accent : C.paper, { sx, sy, alpha: Math.min(1, k * 1.5) });
  });
  ctx.restore();

  // --- the week: seven bars rise from the bottom (u 4..6.5), fold into the underline (u 7.5..8.2)
  const barW = 54, barGap = 26, n = 7;
  const groupW = n * barW + (n - 1) * barGap;
  const x0 = (W - groupW) / 2;
  const baseY = H - safe.y;                           // bars stand on the bottom safe edge
  const fold = springU(u, 7.5, SPRING.gentle);         // 0 → 1: bars collapse into the underline
  const underY = lineY;
  for (let i = 0; i < n; i++) {
    const rise = springU(u, 4 + i * 0.5, SPRING.bouncy);
    if (rise <= 0) continue;
    const today = i === n - 1;
    const hFull = (today ? 300 : 140 + 22 * i) * rise;
    const x = x0 + i * (barW + barGap);
    const top = lerp(baseY - hFull, underY - 2, fold);
    const bottom = lerp(baseY, underY + 2, fold);
    const lit = today && u >= 7;
    ctx.fillStyle = lit ? C.accent : (today ? C.paper : C.muted);
    rrect(ctx, x, top, barW, Math.max(4, bottom - top), fold > 0.5 ? 0 : 6); ctx.fill();
  }
  // the folded bars become one gold underline the width of the lockup
  if (fold > 0.3) {
    const p = clamp((fold - 0.3) / 0.7);
    const uw = lerp(groupW, L.total * s, p);
    ctx.fillStyle = C.accent;
    ctx.fillRect(W / 2 - uw / 2, underY - 2, uw, 4);
  }

  // --- tagline types on (u 6.25..8.15), right to left, then fades as the lockup returns
  const typed = Math.round(TAGLINE.length * clamp((u - 5.5) / (0.9 / 0.469)));
  if (typed > 0 && u < 7.8) {
    const fade = 1 - E.inQuad(prog(u, 7.3, 7.8));   // gone before the lockup drops through
    const tf = font(72, 500, UI); ctx.font = tf;
    const tw = ctx.measureText(TAGLINE).width;          // centre the full line; it types on from the right
    word(ctx, TAGLINE.slice(0, typed), W / 2 + (EN ? -1 : 1) * tw / 2, H * 0.30 + 190, tf, C.paper, { alpha: fade, left: EN });
  }

  // --- presenter line (u 8..): small, under the underline
  const pk = springU(u, 8, SPRING.gentle);
  if (pk > 0) {
    word(ctx, PRESENTER, EN ? lineL : lineR, lineY + 96 + (1 - pk) * 24, font(58, 500, UI), C.paper, { alpha: 0.85 * pk, left: EN });
  }
}

M.film({
  fonts: [font(SIZE, 800, DISPLAY), font(50, 500, UI)],
  hits: HITS,
  draw(ctx, u) { draw(ctx, u); },
});
