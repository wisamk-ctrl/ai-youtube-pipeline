"""The weekly episode's review issue ("Review: … (<week>)"): the chained steps report there.

  ready <week-en>  : the rendered episode and its Shorts are on the previews branch; reply `publish`
  note <week> <text>: any other line"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def issue_for(week: str) -> str:
    repo, base = os.environ["GITHUB_REPOSITORY"], week.removesuffix("-en")
    out = subprocess.run(["gh", "issue", "list", "--repo", repo, "--state", "open", "--search", f"Review: in:title {base}",
                          "--json", "number,title", "--jq",
                          f'[.[] | select(.title | endswith("({week})") or endswith("({base})"))][0].number'],
                         capture_output=True, text=True).stdout.strip()
    return "" if out in ("", "null") else out


def comment(week: str, body: str) -> None:
    repo, num = os.environ["GITHUB_REPOSITORY"], issue_for(week)
    if num:
        subprocess.run(["gh", "issue", "comment", num, "--repo", repo, "--body", body], check=True)
    else:
        subprocess.run(["gh", "issue", "create", "--repo", repo, "--title", f"Review: episode ({week})", "--body", body],
                       check=True)


def main(kind: str, week: str, extra: str = "") -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "wisamk-ctrl/ai-youtube-pipeline")
    raw = f"https://github.com/{repo}/raw/previews"
    if kind == "ready":
        body = (f"**Episode ready to check: `{week}`**\n\n"
                f"▶️ Episode: {raw}/{week}.mp4\n"
                f"📱 Shorts: {raw}/{week}-files/short_01.mp4 (02, 03 next to it)\n"
                f"🖼️ Thumbnails: A {raw}/{week}-files/thumbnail.png · B {raw}/{week}-files/thumbnail_b.png "
                "(A is uploaded; add B in YouTube Studio → the video → Test & Compare)\n\n"
                "The previews take a few minutes to appear. When you are happy, reply here with:\n\n"
                "```\npublish\n```\n\nIt uploads unlisted and goes public at the Sunday slot (17:00 Gulf); "
                "LinkedIn and Facebook follow when it is public. No reply, no upload." + (f"\n\n{extra}" if extra else ""))
        from scripts.notify import whatsapp
        whatsapp(f"AI This Week: the episode {week} is rendered. Check it and reply publish on the review issue.\n{raw}/{week}.mp4")
    else:
        body = extra
    comment(week, body)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], " ".join(sys.argv[3:]))
