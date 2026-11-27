// The rules of TikTok's Content Sharing Guidelines for a Direct Post screen, plus the sealed session cookie.
// developers.tiktok.com/doc/content-sharing-guidelines
import crypto from "node:crypto";

export const SCOPES = ["user.info.basic", "video.publish"];
export const TT = "https://open.tiktokapis.com";

export function authorizeUrl({ clientKey, redirectUri, state }) {
  const q = new URLSearchParams({ client_key: clientKey, scope: SCOPES.join(","), response_type: "code",
    redirect_uri: redirectUri, state });
  return `https://www.tiktok.com/v2/auth/authorize/?${q}`;
}

export function consentLine(branded) {
  return branded
    ? "By posting, you agree to TikTok's Branded Content Policy and Music Usage Confirmation."
    : "By posting, you agree to TikTok's Music Usage Confirmation.";
}

/** The post_info TikTok receives. Throws (with a message for the creator) when the screen's rules are broken. */
export function buildPostInfo(f, creator) {
  const options = creator.privacy_level_options || [];
  if (!f.privacy || !options.includes(f.privacy)) throw new Error("Choose who can view this video (privacy).");
  if (f.commercial && !f.yourBrand && !f.branded)
    throw new Error("Commercial content is on: choose Your brand, Branded content, or both.");
  if (f.commercial && f.branded && f.privacy === "SELF_ONLY")
    throw new Error("Branded content can't be private: choose another privacy setting.");
  if (creator.max_video_post_duration_sec && f.durationSec > creator.max_video_post_duration_sec)
    throw new Error(`This video is too long for your account (max ${creator.max_video_post_duration_sec} s).`);
  return {
    title: String(f.title || "").slice(0, 2200),
    privacy_level: f.privacy,
    disable_comment: creator.comment_disabled || !f.comment,
    disable_duet: creator.duet_disabled || !f.duet,
    disable_stitch: creator.stitch_disabled || !f.stitch,
    brand_organic_toggle: Boolean(f.commercial && f.yourBrand),
    brand_content_toggle: Boolean(f.commercial && f.branded),
    is_aigc: Boolean(f.aigc),
  };
}

function key(secret) { return crypto.createHash("sha256").update("tiktok-session:" + secret).digest(); }

export function seal(obj, secret) {
  const iv = crypto.randomBytes(12), c = crypto.createCipheriv("aes-256-gcm", key(secret), iv);
  const body = Buffer.concat([c.update(JSON.stringify(obj), "utf8"), c.final()]);
  return Buffer.concat([iv, c.getAuthTag(), body]).toString("base64url");
}

export function open(box, secret) {
  try {
    const raw = Buffer.from(box, "base64url");
    const d = crypto.createDecipheriv("aes-256-gcm", key(secret), raw.subarray(0, 12));
    d.setAuthTag(raw.subarray(12, 28));
    return JSON.parse(Buffer.concat([d.update(raw.subarray(28)), d.final()]).toString("utf8"));
  } catch { return null; }
}
