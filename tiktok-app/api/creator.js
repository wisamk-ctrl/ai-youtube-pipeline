import { json, session, tt } from "../lib/http.mjs";
// Who is posting, and what their account allows (TikTok: query this before every post screen).
export default async function handler(req, res) {
  const s = session(req);
  if (!s) return json(res, 401, { error: "not connected" });
  try { json(res, 200, await tt("/v2/post/publish/creator_info/query/", s.access_token)); }
  catch (e) { json(res, 502, { error: String(e.message || e) }); }
}
