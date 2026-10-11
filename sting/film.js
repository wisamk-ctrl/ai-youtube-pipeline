// أسبوع الذكاء الاصطناعي — intro sting. Pure function of time: window.seek(t) paints frame t.
// Timing in beats (u) on the 128 bpm grid in beats.json; docs/shotlist.md is the plan.
import * as M from './lib/motion.js';

const { W, H, FORMAT, E, prog, lerp, clamp, springU, springKeys, SPRING, wobble, font, fill, rrect } = M;

// assets/brand.json — one accent.
const C = { navy: '#0B1220', paper: '#F4F1EA', accent: '#E9B44C', muted: '#5C6B86' };
const DISPLAY = 'Display', UI = 'UI';
const TITLE = ['أسبوع', 'الذكاء', 'الاصطناعي'];          // reading order, right to left
const TAGLINE = 'نشرة أسبوعية لقادة الأعمال والتقنية';
const PRESENTER = 'مع وسام';

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
function word(ctx, str, x, y, f, color, { sx = 1, sy = 1, alpha = 1 } = {}) {
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(x, y); ctx.scale(sx, sy);
  ctx.font = f; ctx.fillStyle = color; ctx.textAlign = 'right'; ctx.direction = 'rtl';
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
function draw(ctx, u) {
  fill(ctx, C.navy);
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
    const xr = wordRight(L.ws, i, right0, GAP);
    let x = xr, y = lineY0, sx = 1, sy = 1;
    if (i === 0) { y = lineY0 - (1 - k) * 220; const q = 0.05 * wobble((u - 0.5) * 0.469, 2.6, 7); sx = 1 + q; sy = 1 - q; }
    else x = xr - (1 - Math.min(k, 1)) * 360;
    word(ctx, w, x, y, f, i === 2 ? C.accent : C.paper, { sx, sy, alpha: Math.min(1, k * 1.5) });
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
    word(ctx, TAGLINE.slice(0, typed), W / 2 + tw / 2, H * 0.30 + 190, tf, C.paper, { alpha: fade });
  }

  // --- presenter line (u 8..): small, under the underline
  const pk = springU(u, 8, SPRING.gentle);
  if (pk > 0) {
    word(ctx, PRESENTER, lineR, lineY + 96 + (1 - pk) * 24, font(58, 500, UI), C.paper, { alpha: 0.85 * pk });
  }
}

M.film({
  fonts: [font(SIZE, 800, DISPLAY), font(50, 500, UI)],
  hits: HITS,
  draw(ctx, u) { draw(ctx, u); },
});
