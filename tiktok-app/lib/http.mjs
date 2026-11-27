// Shared helpers for the functions: the sealed session cookie and TikTok API calls.
import { open, seal, TT } from "./core.mjs";

const SECRET = () => process.env.TIKTOK_CLIENT_SECRET || "";
export const base = (req) => process.env.PUBLIC_URL || `https://${req.headers.host}`;

export function cookies(req) {
  return Object.fromEntries((req.headers.cookie || "").split(/;\s*/).filter(Boolean).map((c) => {
    const i = c.indexOf("="); return [c.slice(0, i), decodeURIComponent(c.slice(i + 1))];
  }));
}
export function setCookie(res, name, value, maxAge) {
  const prev = [].concat(res.getHeader("Set-Cookie") || []);
  res.setHeader("Set-Cookie", [...prev,
    `${name}=${encodeURIComponent(value)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`]);
}
export const session = (req) => { const c = cookies(req).tt; return c ? open(c, SECRET()) : null; };
export const saveSession = (res, s) => setCookie(res, "tt", seal(s, SECRET()), 60 * 60 * 24);

export async function tt(path, token, body) {
  const r = await fetch(TT + path, { method: "POST", headers: { Authorization: `Bearer ${token}`,
    "Content-Type": "application/json; charset=UTF-8" }, body: JSON.stringify(body || {}) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || (j.error && j.error.code && j.error.code !== "ok"))
    throw new Error((j.error && (j.error.message || j.error.code)) || `TikTok HTTP ${r.status}`);
  return j.data;
}
export const json = (res, code, obj) => { res.statusCode = code; res.setHeader("Content-Type", "application/json"); res.end(JSON.stringify(obj)); };
export async function readBody(req) {
  if (req.body) return typeof req.body === "string" ? JSON.parse(req.body) : req.body;
  let s = ""; for await (const ch of req) s += ch; return s ? JSON.parse(s) : {};
}
