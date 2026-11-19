"""Add the partnerships line to the description of every video already on the channel (founder 2026-11-19).

    python scripts/youtube_partnerships.py          → lists what would change (nothing is written)
    python scripts/youtube_partnerships.py apply    → updates each description that lacks the line

The address comes from publish.partnerships_email in config/settings.yaml. New uploads get it from the
description builder; this is for the videos uploaded before. A description that already carries the address is
left alone, so running it twice changes nothing."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LIMIT = 5000   # YouTube's description limit


def with_line(desc: str, email: str) -> str | None:
    """The description with the partnerships line before the hashtags, or None when nothing should change."""
    if email.lower() in desc.lower():
        return None
    line = f"Partnerships: {email}"
    lines = desc.rstrip().splitlines()
    if lines and lines[-1].lstrip().startswith("#"):   # keep the hashtags last
        new = "\n".join(lines[:-1]).rstrip() + f"\n\n{line}\n\n{lines[-1]}"
    else:
        new = desc.rstrip() + f"\n\n{line}"
    return new if len(new) <= LIMIT else None


def main(apply: bool) -> int:
    import yaml
    from pipeline.google_auth import client
    email = str((yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8")).get("publish") or {})
                .get("partnerships_email") or "").strip()
    if not email:
        sys.exit("Set publish.partnerships_email in config/settings.yaml first.")
    yt = client("youtube")
    uploads = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]["contentDetails"][
        "relatedPlaylists"]["uploads"]
    ids, token = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            break
    changed = 0
    for k in range(0, len(ids), 50):
        for v in yt.videos().list(part="snippet", id=",".join(ids[k:k + 50])).execute().get("items", []):
            sn = v["snippet"]
            new = with_line(sn.get("description", ""), email)
            if new is None:
                print(f"= {sn['title'][:70]}")
                continue
            changed += 1
            print(f"{'✏️' if apply else '→'} {sn['title'][:70]}")
            if apply:
                body = {"id": v["id"], "snippet": {"title": sn["title"], "description": new,
                                                   "categoryId": sn.get("categoryId", "28"),
                                                   **({"tags": sn["tags"]} if sn.get("tags") else {}),
                                                   **({"defaultLanguage": sn["defaultLanguage"]} if sn.get("defaultLanguage") else {})}}
                yt.videos().update(part="snippet", body=body).execute()
    print(f"{changed} of {len(ids)} videos {'updated' if apply else 'would change'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(len(sys.argv) > 1 and sys.argv[1] == "apply"))
