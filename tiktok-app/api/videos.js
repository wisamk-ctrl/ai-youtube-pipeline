import { json, session } from "../lib/http.mjs";
// The show's own finished Shorts: the mp4 files attached to the pipeline's GitHub releases.
const REPO = process.env.VIDEO_REPO || "wisamk-ctrl/ai-youtube-pipeline";
export default async function handler(req, res) {
  if (!session(req)) return json(res, 401, { error: "not connected" });
  const r = await fetch(`https://api.github.com/repos/${REPO}/releases?per_page=15`, { headers: { Accept: "application/vnd.github+json" } });
  if (!r.ok) return json(res, 502, { error: `GitHub HTTP ${r.status}` });
  const vids = (await r.json()).flatMap((rel) => rel.assets.filter((a) => /short.*\.mp4$/i.test(a.name))
    .map((a) => ({ name: a.name, url: a.browser_download_url, size: a.size, title: rel.name || rel.tag_name })));
  json(res, 200, vids.slice(0, 20));
}
