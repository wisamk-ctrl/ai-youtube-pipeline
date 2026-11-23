"""Tell the founder about a breaking Short on the "Breaking Shorts" issue (GitHub notifies him).

  drafted <week>  : the script, with its sources, while the video renders
  ready <week>    : the link to watch it, and how to approve
  posted <week> <text> : where it went"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))   # `python scripts/breaking_issue.py` must find the scripts package
TITLE = "Breaking Shorts"


def comment(body: str) -> None:
    repo = os.environ["GITHUB_REPOSITORY"]
    num = subprocess.run(["gh", "issue", "list", "--repo", repo, "--state", "open", "--search", f'"{TITLE}" in:title',
                          "--json", "number,title", "--jq", f'[.[] | select(.title == "{TITLE}")][0].number'],
                         capture_output=True, text=True).stdout.strip()
    if num and num != "null":
        subprocess.run(["gh", "issue", "comment", num, "--repo", repo, "--body", body], check=True)
    else:
        subprocess.run(["gh", "issue", "create", "--repo", repo, "--title", TITLE, "--body", body], check=True)


def main(kind: str, week: str, extra: str = "") -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "wisamk-ctrl/ai-youtube-pipeline")
    folder = ROOT / "reviewed" / week
    if kind == "drafted":
        src = (folder / "sources_ok.txt").read_text(encoding="utf-8") if (folder / "sources_ok.txt").exists() else ""
        what = "explainer Short (from the approved ranking)" if "-exp-" in week else "breaking Short"
        body = (f"**New {what} drafted: `{week}`**\n\nRendering now (about 5 minutes). The script, line by line "
                f"with the article each line rests on:\n\n{src}\n\nI'll post the video link here when it's ready.")
    elif kind == "ready":
        url = f"https://github.com/{repo}/raw/previews/{week}-files/short_01.mp4"
        from pipeline.config import load_settings
        from pipeline.publish.social import channels_line
        where = channels_line(load_settings())
        body = (f"**Ready to check: `{week}`**\n\n▶️ {url}\n\nTo publish to {where}, reply here with:\n\n"
                f"```\npost {week}\n```\n\nNo reply, no post." + (f"\n\n{extra}" if extra else ""))
    else:
        body = f"**Posted: `{week}`**\n\n{extra}"
    comment(body)
    from scripts.notify import whatsapp
    issue = f"https://github.com/{repo}/issues?q=is%3Aopen+%22Breaking+Shorts%22+in%3Atitle"
    whatsapp({"drafted": f"AI This Week: breaking Short script ready, video rendering (~10 min).\n{week}\nScript and sources: {issue}",
              "ready": f"AI This Week: breaking Short ready to check.\n▶️ https://github.com/{repo}/raw/previews/{week}-files/short_01.mp4\n"
                       f"To publish, reply on the Breaking Shorts issue: post {week}\n{issue}"}.get(
        kind, f"AI This Week: posted {week}.\n{extra}"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], " ".join(sys.argv[3:]))
