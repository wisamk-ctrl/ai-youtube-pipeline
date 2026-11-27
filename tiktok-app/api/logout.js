import { setCookie } from "../lib/http.mjs";
export default function handler(req, res) { setCookie(res, "tt", "", 0); res.statusCode = 302; res.setHeader("Location", "/"); res.end(); }
