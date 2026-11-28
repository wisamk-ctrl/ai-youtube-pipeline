// AI This Week · Post to TikTok, on Cloudflare Workers. Static page from ./public; the API below.
// Secrets (wrangler secret put): TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET.
import crypto from "node:crypto";
import { authorizeUrl, buildPostInfo, open, seal, TT } from "../lib/core.mjs";

const REPO = "wisamk-ctrl/ai-youtube-pipeline";
const json = (obj, status = 200, headers = {}) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json", ...headers } });
const redirect = (to, headers = {}) => new Response(null, { status: 302, headers: { Location: to, ...headers } });
const cookie = (name, value, maxAge) =>
  `${name}=${encodeURIComponent(value)}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
function cookies(req) {
  return Object.fromEntries((req.headers.get("Cookie") || "").split(/;\s*/).filter(Boolean).map((c) => {
    const i = c.indexOf("="); return [c.slice(0, i), decodeURIComponent(c.slice(i + 1))];
  }));
}

async function tt(path, token, body) {
  const r = await fetch(TT + path, { method: "POST", headers: { Authorization: `Bearer ${token}`,
    "Content-Type": "application/json; charset=UTF-8" }, body: JSON.stringify(body || {}) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || (j.error && j.error.code && j.error.code !== "ok"))
    throw new Error(j.error ? `${j.error.code}: ${j.error.message || ""}`.trim() : `TikTok HTTP ${r.status}`);
  return j.data;
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url), base = url.origin, callback = `${base}/api/callback`;
    const s = cookies(req).tt ? open(cookies(req).tt, env.TIKTOK_CLIENT_SECRET) : null;
    try {
      switch (url.pathname) {
        case "/api/login": {
          const state = crypto.randomBytes(16).toString("hex");
          return redirect(authorizeUrl({ clientKey: env.TIKTOK_CLIENT_KEY, redirectUri: callback, state }),
            { "Set-Cookie": cookie("tt_state", state, 600) });
        }
        case "/api/callback": {
          const back = (m) => redirect("/?error=" + encodeURIComponent(m));
          if (url.searchParams.get("error")) return back(url.searchParams.get("error_description") || "TikTok login was cancelled.");
          if (!url.searchParams.get("state") || url.searchParams.get("state") !== cookies(req).tt_state) return back("Login expired, please try again.");
          const r = await fetch(`${TT}/v2/oauth/token/`, { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ client_key: env.TIKTOK_CLIENT_KEY, client_secret: env.TIKTOK_CLIENT_SECRET,
              code: url.searchParams.get("code") || "", grant_type: "authorization_code", redirect_uri: callback }) });
          const t = await r.json().catch(() => ({}));
          if (!t.access_token) return back(t.error_description || "TikTok did not return an access token.");
          const h = new Headers({ Location: "/" });
          h.append("Set-Cookie", cookie("tt_state", "", 0));
          h.append("Set-Cookie", cookie("tt", seal({ access_token: t.access_token, open_id: t.open_id }, env.TIKTOK_CLIENT_SECRET), 86400));
          return new Response(null, { status: 302, headers: h });
        }
        case "/api/logout": return redirect("/", { "Set-Cookie": cookie("tt", "", 0) });
      }
      if (!url.pathname.startsWith("/api/")) return env.ASSETS.fetch(req);
      if (!s) return json({ error: "not connected" }, 401);
      switch (url.pathname) {
        case "/api/creator": return json(await tt("/v2/post/publish/creator_info/query/", s.access_token));
        case "/api/videos": {
          const r = await fetch(`https://api.github.com/repos/${REPO}/releases?per_page=15`,
            { headers: { Accept: "application/vnd.github+json", "User-Agent": "aithisweek-post" } });
          if (!r.ok) return json({ error: `GitHub HTTP ${r.status}` }, 502);
          const vids = (await r.json()).flatMap((rel) => rel.assets.filter((a) => /short.*\.mp4$/i.test(a.name))
            .map((a) => ({ name: a.name, url: a.browser_download_url, size: a.size, title: rel.name || rel.tag_name })));
          const list = vids.slice(0, 20);
          await Promise.all(list.map(async (v) => {   // the Short's own headline, from the week's breaking.yaml
            const week = v.name.replace(/-short-\d+\.mp4$/i, "");
            const y = await fetch(`https://raw.githubusercontent.com/${REPO}/main/reviewed/${week}/breaking.yaml`).catch(() => null);
            const m = y && y.ok ? (await y.text()).match(/^title:\s*['"]?(.+?)['"]?\s*$/m) : null;
            v.title = m ? m[1] : week;
          }));
          return json(list);
        }
        case "/api/post": {
          if (req.method !== "POST") return json({ error: "POST only" }, 405);
          const { videoUrl, form } = await req.json();
          if (!String(videoUrl).startsWith(`https://github.com/${REPO}/releases/download/`)) throw new Error("Unknown video.");
          const creator = await tt("/v2/post/publish/creator_info/query/", s.access_token);
          const post_info = buildPostInfo(form, creator);
          const v = await fetch(videoUrl);
          if (!v.ok) throw new Error(`Could not fetch the video (HTTP ${v.status}).`);
          const buf = new Uint8Array(await v.arrayBuffer());
          if (buf.length > 64 * 1024 * 1024) throw new Error("Video over 64 MB.");
          const init = await tt("/v2/post/publish/video/init/", s.access_token, { post_info,
            source_info: { source: "FILE_UPLOAD", video_size: buf.length, chunk_size: buf.length, total_chunk_count: 1 } });
          const up = await fetch(init.upload_url, { method: "PUT", body: buf, headers: { "Content-Type": "video/mp4",
            "Content-Range": `bytes 0-${buf.length - 1}/${buf.length}` } });
          if (!up.ok) throw new Error(`Upload to TikTok failed (HTTP ${up.status}).`);
          return json({ publish_id: init.publish_id });
        }
        case "/api/status": {
          const { publish_id } = await req.json();
          return json(await tt("/v2/post/publish/status/fetch/", s.access_token, { publish_id }));
        }
      }
      return json({ error: "not found" }, 404);
    } catch (e) {
      return json({ error: String(e.message || e) }, 400);
    }
  },
};
