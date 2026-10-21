"""List the HeyGen avatars and voices the API key can use, so the IDs can be chosen
without pasting the key anywhere. Writes heygen_assets.json and prints a markdown report
(custom avatars and talking photos first, Arabic voices first). Never prints the key."""

from __future__ import annotations

import json
import os
import sys

import requests

BASE = "https://api.heygen.com"


def get(session: requests.Session, path: str) -> dict:
    r = session.get(f"{BASE}{path}", timeout=60)
    if r.status_code != 200:
        sys.exit(f"{path} → HTTP {r.status_code}: {r.text[:300]}")
    return r.json().get("data") or {}


def main() -> None:
    key = os.environ.get("HEYGEN_API_KEY", "")
    if not key:
        sys.exit("HEYGEN_API_KEY is not set")
    s = requests.Session()
    s.headers.update({"X-Api-Key": key, "Accept": "application/json"})
    av = get(s, "/v2/avatars")
    vo = get(s, "/v2/voices")
    avatars = av.get("avatars") or []
    photos = av.get("talking_photos") or []
    voices = vo.get("voices") or []
    json.dump({"avatars": avatars, "talking_photos": photos, "voices": voices},
              open("heygen_assets.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    custom = [a for a in avatars if a.get("premium") is False and a.get("is_public") is False] or \
             [a for a in avatars if not a.get("is_public", True)]
    public = [a for a in avatars if a not in custom]
    arabic = [v for v in voices if "arab" in (v.get("language") or "").lower()]
    other = [v for v in voices if v not in arabic]

    out = [f"## HeyGen assets\n\n{len(avatars)} avatars · {len(photos)} talking photos · {len(voices)} voices "
           f"({len(arabic)} Arabic). Full list in the `heygen-assets` artifact.\n"]
    out.append("### Your avatars (custom / instant)\n")
    out.append("| avatar_id | name | gender |\n|---|---|---|")
    out += [f"| `{a.get('avatar_id')}` | {a.get('avatar_name')} | {a.get('gender')} |" for a in custom] or ["| — | none | |"]
    out.append(f"\n### Your talking photos (use `avatar_type: talking_photo`; first 40 of {len(photos)}, rest in the artifact)\n")
    out.append("| talking_photo_id | name |\n|---|---|")
    out += [f"| `{p.get('talking_photo_id')}` | {p.get('talking_photo_name')} |" for p in photos[:40]] or ["| — | none | |"]
    out.append(f"\n### Public avatars (first 40 of {len(public)})\n")
    out.append("| avatar_id | name | gender |\n|---|---|---|")
    out += [f"| `{a.get('avatar_id')}` | {a.get('avatar_name')} | {a.get('gender')} |" for a in public[:40]]
    out.append("\n### Arabic voices\n")
    out.append("| voice_id | name | gender | language | preview |\n|---|---|---|---|---|")
    out += [f"| `{v.get('voice_id')}` | {v.get('name')} | {v.get('gender')} | {v.get('language')} | "
            f"{('[listen](' + v['preview_audio'] + ')') if v.get('preview_audio') else ''} |" for v in arabic] or ["| — | none | | | |"]
    out.append(f"\n<details><summary>Other voices ({len(other)})</summary>\n\n| voice_id | name | language |\n|---|---|---|")
    out += [f"| `{v.get('voice_id')}` | {v.get('name')} | {v.get('language')} |" for v in other[:150]]
    out.append("</details>")
    report = "\n".join(out)
    open("heygen_assets.md", "w", encoding="utf-8").write(report)
    print(report[:4000])


if __name__ == "__main__":
    main()
