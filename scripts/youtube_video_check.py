"""After an upload: is the video processed, and does each chapter show its own picture?

Founder 2026-11-18: on the W46-en episode every chapter in YouTube's chapter list showed the video's thumbnail
instead of a frame from that chapter. YouTube makes those chapter pictures itself (no API sets them), so this
reads what YouTube actually shows: the processing state from the Data API, and the chapter list with its
pictures from the watch page. Exit 1 when two or more chapters show the same picture.

Usage: python scripts/youtube_video_check.py <video id>"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}


def processing(video_id: str) -> dict:
    keys = ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
    if not all(os.environ.get(k) for k in keys):
        return {}
    tok = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"], "grant_type": "refresh_token"}).json()["access_token"]
    r = requests.get("https://www.googleapis.com/youtube/v3/videos", timeout=30, headers={"Authorization": f"Bearer {tok}"},
                     params={"part": "status,processingDetails,contentDetails", "id": video_id}).json()
    return (r.get("items") or [{}])[0]


def chapters(html: str) -> list[dict]:
    """Every chapter YouTube shows: title, start, picture URL (from the page's ytInitialData)."""
    m = re.search(r"var ytInitialData\s*=\s*(\{.*?\});</script>", html, re.S)
    if not m:
        return []
    out: list[dict] = []

    def walk(o):
        if isinstance(o, dict):
            c = o.get("chapterRenderer")
            if isinstance(c, dict):
                thumbs = (c.get("thumbnail") or {}).get("thumbnails") or []
                out.append({"title": (c.get("title") or {}).get("simpleText", ""),
                            "start": int(c.get("timeRangeStartMillis") or 0) / 1000,
                            "picture": thumbs[-1]["url"] if thumbs else ""})
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(json.loads(m.group(1)))
    seen, uniq = set(), []
    for c in out:
        if (c["title"], c["start"]) not in seen:
            seen.add((c["title"], c["start"]))
            uniq.append(c)
    return uniq


def main(video_id: str) -> int:
    v = processing(video_id)
    if v:
        p = v.get("processingDetails") or {}
        print("Processing:", p.get("processingStatus"), "| thumbnails:", p.get("thumbnailsAvailability"),
              "| privacy:", (v.get("status") or {}).get("privacyStatus"), "| definition:",
              (v.get("contentDetails") or {}).get("definition"), "| rating:",
              ((v.get("contentDetails") or {}).get("contentRating") or {}).get("ytRating", "none"),
              "| made for kids:", (v.get("status") or {}).get("madeForKids"))
    html = requests.get(f"https://www.youtube.com/watch?v={video_id}", headers=UA, timeout=60).text
    import re
    m = re.search(r'"playabilityStatus":\{"status":"([A-Z_]+)"', html)
    why = re.search(r'"playabilityStatus":\{[^{}]*?"reason":"([^"]+)"', html)
    print("Watch page as seen from here:", m.group(1) if m else "no player data", "|", len(html), "bytes",
          "|", why.group(1) if why else "")
    print("Storyboard (frame previews) on the page:", "yes" if "playerStoryboardSpecRenderer" in html else "no")
    ch = chapters(html)
    if not ch:
        print("No chapters found on the watch page.")
        return 1
    digests = {}
    for c in ch:
        img = requests.get(c["picture"], headers=UA, timeout=60).content if c["picture"] else b""
        d = hashlib.md5(img).hexdigest()[:10] if img else "none"
        digests.setdefault(d, []).append(c["title"])
        print(f"{int(c['start'] // 60)}:{int(c['start'] % 60):02d}  {c['title'][:50]:<50}  picture {d}  {c['picture'][:90]}")
    same = [t for t in digests.values() if len(t) > 1]
    if same:
        print(f"FAIL: chapters share a picture: {same}")
        return 1
    print(f"OK: {len(ch)} chapters, each with its own picture")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
