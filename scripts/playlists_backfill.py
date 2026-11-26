"""Put every public video already on the channel into its playlists (pipeline/publish/playlists.py).

    python scripts/playlists_backfill.py           # preview: prints where each video would go
    python scripts/playlists_backfill.py apply      # adds them (creates missing playlists)

New videos are placed at upload (Shorts) and at release (episodes); this is for the ones before that."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def seconds(iso: str) -> int:
    m = re.fullmatch(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return int(m[1] or 0) * 3600 + int(m[2] or 0) * 60 + int(m[3] or 0) if m else 0


def main(apply: bool) -> int:
    from pipeline.config import load_settings
    from pipeline.google_auth import client
    from pipeline.publish import playlists as pl
    cfg, yt = load_settings(), client("youtube")
    uploads = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0][
        "contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while True:
        res = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50,
                                      pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in res.get("items", [])]
        token = res.get("nextPageToken")
        if not token:
            break
    have = pl.existing(yt) if apply else {}
    for k in range(0, len(ids), 50):
        for v in yt.videos().list(part="snippet,status,contentDetails", id=",".join(ids[k:k + 50])).execute()["items"]:
            if v["status"].get("privacyStatus") != "public":
                continue
            kind = "short" if seconds(v["contentDetails"].get("duration")) <= 180 else "episode"
            sn = v["snippet"]
            if apply:
                got = pl.place(yt, v["id"], sn["title"], sn.get("description", ""), kind, cfg, have)
            else:
                got = pl.pick(sn["title"], sn.get("description", ""), kind, cfg)
            print(f"{kind:7} {v['id']}  {sn['title'][:60]:60}  → {', '.join(got) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(len(sys.argv) > 1 and sys.argv[1] == "apply"))
