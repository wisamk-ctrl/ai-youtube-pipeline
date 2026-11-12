"""Contact sheets of the tracked YouTube channels' latest thumbnails (design reference for our own).

One row per channel, newest first, the channel's name on the left; titles go to titles.md.
Usage: YOUTUBE_API_KEY=… python scripts/thumb_survey.py <out dir> [per channel]
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main(out: Path, per: int = 4) -> None:
    key = os.environ["YOUTUBE_API_KEY"]
    cfg = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))
    ids = json.loads((ROOT / "data" / "youtube_channels.json").read_text(encoding="utf-8"))
    chans = next(v for v in _walk(cfg) if isinstance(v, dict) and "channels" in v and "max_per_channel" in v)["channels"]
    out.mkdir(parents=True, exist_ok=True)
    rows, titles = [], []
    for c in chans:
        cid = c.get("channel_id") or ids.get(str(c.get("handle", "")).lower())
        if not cid:
            continue
        r = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", timeout=30, params={
            "part": "snippet", "playlistId": "UU" + cid[2:], "maxResults": per, "key": key})
        if r.status_code != 200:
            print(f"{c['name']}: HTTP {r.status_code}")
            continue
        files = []
        titles.append(f"## {c['name']}")
        for n, it in enumerate(r.json().get("items", [])):
            sn = it["snippet"]
            th = sn["thumbnails"]
            url = (th.get("maxres") or th.get("standard") or th.get("high") or th["default"])["url"]
            f = out / f"{c['handle']}_{n}.jpg"
            f.write_bytes(requests.get(url, timeout=30).content)
            files.append(f)
            titles.append(f"- {sn['title']}")
        if not files:
            continue
        row = out / f"row_{c['handle']}.jpg"
        ins = [x for f in files for x in ("-i", str(f))]
        scale = "".join(f"[{i}:v]scale=480:270:force_original_aspect_ratio=increase,crop=480:270[v{i}];" for i in range(len(files)))
        label = c["name"].replace("'", "").replace(":", "")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ins, "-filter_complex",
                        scale + "".join(f"[v{i}]" for i in range(len(files))) + f"hstack=inputs={len(files)}"
                        + (",pad=1920:270:0:0" if len(files) < per else "")
                        + f",drawtext=text='{label}':fontcolor=white:fontsize=26:x=10:y=8:box=1:boxcolor=black@0.75:boxborderw=6",
                        "-frames:v", "1", str(row)], check=True)
        rows.append(row)
    for n in range(0, len(rows), 5):       # five channels per sheet keeps each thumbnail readable
        part = rows[n:n + 5]
        ins = [x for f in part for x in ("-i", str(f))]
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ins, "-filter_complex",
                        f"vstack=inputs={len(part)}" if len(part) > 1 else "null", "-frames:v", "1",
                        str(out / f"sheet-{n // 5 + 1}.jpg")], check=True)
    (out / "titles.md").write_text("\n".join(titles) + "\n", encoding="utf-8")
    for f in out.glob("*_[0-9].jpg"):
        f.unlink()
    for f in rows:
        f.unlink()


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


if __name__ == "__main__":
    main(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 4)
