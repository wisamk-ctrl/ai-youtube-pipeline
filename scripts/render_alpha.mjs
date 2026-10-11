#!/usr/bin/env node
// Render a transparent-canvas film (lowerthird/) to an alpha PNG sequence, then encode:
//   out/lowerthird/<name>.mov   ProRes 4444 with alpha (Premiere / Resolve / FCP)
//   out/lowerthird/<name>.webm  VP9 with alpha (web, CapCut, DaVinci free)
//   out/lowerthird/<name>_hold.png  one still from the hold (for a static overlay / thumbnails)
//
//   node scripts/render_alpha.mjs --film lowerthird --name "وسام" --title "أسبوع الذكاء الاصطناعي" --dur 6 --out presenter
//
// Frames are rendered through Playwright's page.screenshot({ omitBackground: true }); each frame is
// window.seek(t), so the film must stay a pure function of time.
import { chromium } from 'playwright';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
const film = arg('film', 'lowerthird'), out = arg('out', 'lowerthird'), dur = Number(arg('dur', 6)), fps = 60;
const query = new URLSearchParams({ render: '1', dur: String(dur), name: arg('name', 'وسام'), title: arg('title', 'أسبوع الذكاء الاصطناعي') });

const outDir = path.resolve('out', film), frames = path.join(outDir, `frames_${out}`);
fs.mkdirSync(frames, { recursive: true });

const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });  // @font-face over file://
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
page.on('pageerror', (e) => console.error('[page]', e.message));
page.on('console', (m) => { if (m.type() === 'error') console.error('[console]', m.text()); });
await page.goto(`file://${path.resolve(film, 'index.html')}?${query}`);
await page.waitForFunction(() => window.filmReady === true, null, { timeout: 20000 });

const n = Math.round(dur * fps);
for (let i = 0; i < n; i++) {
  await page.evaluate((t) => window.seek(t), i / fps);
  await page.screenshot({ path: path.join(frames, `f${String(i).padStart(5, '0')}.png`), omitBackground: true, clip: { x: 0, y: 0, width: 1920, height: 1080 } });
  if (i % 60 === 0) process.stdout.write(`\r${i}/${n} frames`);
}
await browser.close();
console.log(`\r${n}/${n} frames rendered`);

const ff = (...a) => { const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...a], { stdio: 'inherit' }); if (r.status) process.exit(r.status); };
const seq = path.join(frames, 'f%05d.png');
ff('-framerate', String(fps), '-i', seq, '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', path.join(outDir, `${out}.mov`));
ff('-framerate', String(fps), '-i', seq, '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '24', '-auto-alt-ref', '0', path.join(outDir, `${out}.webm`));
fs.copyFileSync(path.join(frames, `f${String(Math.round(dur * fps / 2)).padStart(5, '0')}.png`), path.join(outDir, `${out}_hold.png`));
fs.rmSync(frames, { recursive: true, force: true });
console.log(`-> ${outDir}/${out}.mov  ${out}.webm  ${out}_hold.png`);
