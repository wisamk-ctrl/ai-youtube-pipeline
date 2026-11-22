"""Rewrite the links in a published video's description to the publisher's own, cleaned address (founder 2026-11-22).

    python scripts/youtube_short_links.py <video id>          → shows what would change (nothing is written)
    python scripts/youtube_short_links.py <video id> apply    → updates the description and its translations

New uploads get clean links from the description builder (publish/description.py); this is for a video uploaded
before. Only the links change. A link that cannot be resolved is left as it is, so running it twice changes nothing."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

URL = re.compile(r"https?://[^\s<>]+")


def shorten(text: str, resolve=None, timeout: float = 15.0) -> str:
    """The text with every source link cleaned; a Google News link becomes the article's own link."""
    from pipeline.ingestion import articles
    from pipeline.publish.description import clean_url
    resolve = resolve or articles.resolve_google_news

    def one(m: re.Match) -> str:
        url = m.group(0)
        if articles._is_google(url):
            found = resolve(url, timeout)
            return clean_url(found) if found else url
        return url if "youtu" in url else clean_url(url)
    return URL.sub(one, text)


def main(video_id: str, apply: bool) -> int:
    from pipeline.google_auth import client
    yt = client("youtube")
    v = yt.videos().list(part="snippet,localizations", id=video_id).execute()["items"][0]
    sn, loc = v["snippet"], v.get("localizations") or {}
    new = shorten(sn.get("description", ""))
    new_loc = {k: {**x, "description": shorten(x.get("description", ""))} for k, x in loc.items()}
    if new == sn.get("description", "") and new_loc == loc:
        print("= nothing to change")
        return 0
    print(f"{'✏️' if apply else '→'} {sn['title'][:70]}: description {len(sn.get('description', ''))} → {len(new)} characters")
    if apply:
        body = {"id": video_id, "snippet": {"title": sn["title"], "description": new,
                                            "categoryId": sn.get("categoryId", "28"),
                                            **({"tags": sn["tags"]} if sn.get("tags") else {}),
                                            **({"defaultLanguage": sn["defaultLanguage"]} if sn.get("defaultLanguage") else {})}}
        part = "snippet"
        if new_loc:
            body["localizations"], part = new_loc, "snippet,localizations"
        yt.videos().update(part=part, body=body).execute()
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], len(sys.argv) > 2 and sys.argv[2] == "apply"))
