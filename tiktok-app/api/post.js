import { buildPostInfo } from "../lib/core.mjs";
import { json, readBody, session, tt } from "../lib/http.mjs";
// Direct Post with FILE_UPLOAD: the chosen Short is fetched from the show's releases and sent to TikTok in one chunk.
const REPO = process.env.VIDEO_REPO || "wisamk-ctrl/ai-youtube-pipeline";
export default async function handler(req, res) {
  const s = session(req);
  if (!s) return json(res, 401, { error: "not connected" });
  if (req.method !== "POST") return json(res, 405, { error: "POST only" });
  try {
    const { videoUrl, form } = await readBody(req);
    if (!String(videoUrl).startsWith(`https://github.com/${REPO}/releases/download/`)) throw new Error("Unknown video.");
    const creator = await tt("/v2/post/publish/creator_info/query/", s.access_token);
    const post_info = buildPostInfo(form, creator);
    const v = await fetch(videoUrl);
    if (!v.ok) throw new Error(`Could not fetch the video (HTTP ${v.status}).`);
    const buf = Buffer.from(await v.arrayBuffer());
    if (buf.length > 64 * 1024 * 1024) throw new Error("Video over 64 MB.");
    const init = await tt("/v2/post/publish/video/init/", s.access_token, { post_info,
      source_info: { source: "FILE_UPLOAD", video_size: buf.length, chunk_size: buf.length, total_chunk_count: 1 } });
    const up = await fetch(init.upload_url, { method: "PUT", body: buf, headers: { "Content-Type": "video/mp4",
      "Content-Length": String(buf.length), "Content-Range": `bytes 0-${buf.length - 1}/${buf.length}` } });
    if (!up.ok) throw new Error(`Upload to TikTok failed (HTTP ${up.status}).`);
    json(res, 200, { publish_id: init.publish_id });
  } catch (e) { json(res, 400, { error: String(e.message || e) }); }
}
