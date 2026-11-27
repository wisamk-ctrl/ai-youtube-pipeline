import crypto from "node:crypto";
import { authorizeUrl } from "../lib/core.mjs";
import { base, setCookie } from "../lib/http.mjs";

export default function handler(req, res) {
  const state = crypto.randomBytes(16).toString("hex");
  setCookie(res, "tt_state", state, 600);
  res.statusCode = 302;
  res.setHeader("Location", authorizeUrl({ clientKey: process.env.TIKTOK_CLIENT_KEY, redirectUri: `${base(req)}/api/callback`, state }));
  res.end();
}
