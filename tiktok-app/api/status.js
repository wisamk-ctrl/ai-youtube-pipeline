import { json, readBody, session, tt } from "../lib/http.mjs";
export default async function handler(req, res) {
  const s = session(req);
  if (!s) return json(res, 401, { error: "not connected" });
  try { const { publish_id } = await readBody(req); json(res, 200, await tt("/v2/post/publish/status/fetch/", s.access_token, { publish_id })); }
  catch (e) { json(res, 502, { error: String(e.message || e) }); }
}
