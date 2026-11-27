import { base, cookies, saveSession, setCookie } from "../lib/http.mjs";

export default async function handler(req, res) {
  const u = new URL(req.url, base(req));
  const back = (msg) => { res.statusCode = 302; res.setHeader("Location", "/?error=" + encodeURIComponent(msg)); res.end(); };
  if (u.searchParams.get("error")) return back(u.searchParams.get("error_description") || "TikTok login was cancelled.");
  if (!u.searchParams.get("state") || u.searchParams.get("state") !== cookies(req).tt_state) return back("Login expired, please try again.");
  const r = await fetch("https://open.tiktokapis.com/v2/oauth/token/", { method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_key: process.env.TIKTOK_CLIENT_KEY, client_secret: process.env.TIKTOK_CLIENT_SECRET,
      code: u.searchParams.get("code") || "", grant_type: "authorization_code", redirect_uri: `${base(req)}/api/callback` }) });
  const t = await r.json().catch(() => ({}));
  if (!t.access_token) return back(t.error_description || "TikTok did not return an access token.");
  setCookie(res, "tt_state", "", 0);
  saveSession(res, { access_token: t.access_token, open_id: t.open_id, scope: t.scope });
  res.statusCode = 302; res.setHeader("Location", "/"); res.end();
}
