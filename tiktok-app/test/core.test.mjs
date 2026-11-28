// TikTok's content-sharing rules for a Direct Post screen, checked before any post leaves the app.
import { test } from "node:test";
import assert from "node:assert/strict";
import { authorizeUrl, buildPostInfo, seal, open, consentLine, SCOPES } from "../lib/core.mjs";

const creator = { privacy_level_options: ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"],
  comment_disabled: false, duet_disabled: true, stitch_disabled: false, max_video_post_duration_sec: 600 };
const form = { title: "CIA System Hit by Breach #AI", privacy: "PUBLIC_TO_EVERYONE", comment: false, duet: false,
  stitch: false, commercial: false, yourBrand: false, branded: false, aigc: true, durationSec: 62 };

test("asks only for the scopes the demo shows", () => {
  assert.deepEqual(SCOPES, ["user.info.basic", "video.publish"]);
  const u = new URL(authorizeUrl({ clientKey: "ck", redirectUri: "https://x.app/api/callback", state: "s1" }));
  assert.equal(u.origin + u.pathname, "https://www.tiktok.com/v2/auth/authorize/");
  assert.equal(u.searchParams.get("scope"), "user.info.basic,video.publish");
  assert.equal(u.searchParams.get("state"), "s1");
  assert.equal(u.searchParams.get("disable_auto_auth"), "1");   // the consent screen shows every time
});

test("privacy has no default: posting without a choice is refused", () => {
  assert.throws(() => buildPostInfo({ ...form, privacy: "" }, creator), /privacy/i);
  assert.throws(() => buildPostInfo({ ...form, privacy: "FOLLOWER_OF_CREATOR" }, creator), /privacy/i);
});

test("interactions are off unless the creator turns them on, and stay off where TikTok disabled them", () => {
  const p = buildPostInfo({ ...form, comment: true, duet: true }, creator);
  assert.equal(p.disable_comment, false);
  assert.equal(p.disable_duet, true);      // the creator's account has duets off
  assert.equal(p.disable_stitch, true);    // not ticked
  assert.equal(p.is_aigc, true);
});

test("commercial content needs a type, and branded content cannot be private", () => {
  assert.throws(() => buildPostInfo({ ...form, commercial: true }, creator), /your brand|branded/i);
  assert.throws(() => buildPostInfo({ ...form, commercial: true, branded: true, privacy: "SELF_ONLY" }, creator), /private/i);
  const p = buildPostInfo({ ...form, commercial: true, yourBrand: true }, creator);
  assert.equal(p.brand_organic_toggle, true);
  assert.equal(p.brand_content_toggle, false);
});

test("a video longer than the creator may post is refused", () => {
  assert.throws(() => buildPostInfo({ ...form, durationSec: 601 }, creator), /long/i);
});

test("the consent line names the Branded Content Policy only for branded content", () => {
  assert.match(consentLine(false), /^By posting, you agree to TikTok's Music Usage Confirmation\.$/);
  assert.match(consentLine(true), /Branded Content Policy and Music Usage Confirmation/);
});

test("the session cookie is sealed: unreadable, tamper-evident, round-trips", () => {
  const box = seal({ access_token: "a", open_id: "o" }, "secret-key");
  assert.ok(!box.includes("access_token"));
  assert.deepEqual(open(box, "secret-key"), { access_token: "a", open_id: "o" });
  assert.equal(open(box, "other-key"), null);
  assert.equal(open(box.slice(0, -2) + "xx", "secret-key"), null);
});
