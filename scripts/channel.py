"""The show's weekly health: never miss a week, and learn what works.

    python scripts/channel.py watch-script     Saturday: did this week's script run succeed?
    python scripts/channel.py watch-publish    Sunday, before 11:00 Gulf: is an episode going out today?
    python scripts/channel.py report           Monday: views / likes / comments per video and per Short,
                                               the change since last week, watch time when the token allows

A problem opens (or updates) one issue titled "Show at risk"; GitHub e-mails it to the founder.
The report is posted as an issue "Weekly numbers <date>" and kept in data/channel_stats.json.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
STATS = ROOT / "data" / "channel_stats.json"
API = "https://www.googleapis.com/youtube/v3"
NOW = datetime.now(timezone.utc)


def token() -> str:
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    if r.status_code != 200:
        raise RuntimeError(f"YouTube sign-in failed: {r.json().get('error_description') or r.text[:200]}")
    return r.json()["access_token"]


def get(path: str, tok: str, **params) -> dict:
    r = requests.get(f"{API}/{path}", params=params, headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    r.raise_for_status()
    return r.json()


def videos(tok: str, limit: int = 50) -> list[dict]:
    ch = get("channels", tok, part="contentDetails,statistics,snippet", mine="true")["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in
           get("playlistItems", tok, part="contentDetails", playlistId=uploads, maxResults=limit).get("items", [])]
    out = []
    for n in range(0, len(ids), 50):
        out += get("videos", tok, part="snippet,status,statistics,contentDetails", id=",".join(ids[n:n + 50]))["items"]
    return [dict(v, channel=ch) for v in out]


def seconds(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0)
    return h * 3600 + mi * 60 + s


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def alarm(title: str, body: str) -> None:
    """One open "Show at risk" issue, updated, so a bad week sends one e-mail thread, not a flood."""
    repo = os.environ["GITHUB_REPOSITORY"]
    n = gh("issue", "list", "--repo", repo, "--state", "open", "--search", "Show at risk in:title",
           "--json", "number", "-q", ".[0].number").strip()
    text = f"**{title}** ({NOW:%a %d %b %H:%M} UTC)\n\n{body}\n"
    if n:
        gh("issue", "comment", n, "--repo", repo, "--body", text)
    else:
        gh("issue", "create", "--repo", repo, "--title", "Show at risk", "--body", text)
    print("ALARM:", title)


def watch_script() -> None:
    """Saturday afternoon: this morning's scheduled run (the week's script) must have succeeded."""
    repo = os.environ["GITHUB_REPOSITORY"]
    runs = json.loads(gh("run", "list", "--repo", repo, "--workflow", "weekly.yml", "--event", "schedule",
                         "--limit", "3", "--json", "conclusion,createdAt,url"))
    today = [r for r in runs if r["createdAt"][:10] == NOW.strftime("%Y-%m-%d")]
    if not today:
        alarm("This week's script did not run", "The Saturday run of `weekly` never started. Run it by hand: "
              "Actions → weekly → Run workflow → phase `script`.")
    elif today[0]["conclusion"] != "success":
        alarm("This week's script failed", f"Run: {today[0]['url']} — the failure issue has the reason. "
              "Fix and re-run phase `script`, or the episode will not be ready for Sunday.")
    else:
        print("script ok:", today[0]["url"])


def watch_publish() -> None:
    """Sunday morning: an episode (over 60 s) is scheduled to go public within the next 12 hours, or went
    public in the last 24."""
    vids = videos(token(), 15)
    soon = []
    for v in vids:
        if seconds(v["contentDetails"].get("duration")) <= 60:
            continue
        st = v["status"]
        when = st.get("publishAt") if st.get("privacyStatus") == "private" else v["snippet"].get("publishedAt")
        if not when:
            continue
        t = datetime.fromisoformat(when.replace("Z", "+00:00"))
        if NOW - timedelta(hours=24) <= t <= NOW + timedelta(hours=12):
            soon.append(f"{v['snippet']['title']} ({st.get('privacyStatus')}, {when})")
    if soon:
        print("episode ok:", soon)
    else:
        alarm("No episode is scheduled for today",
              "Nothing on the channel goes public this morning. If the week's edit is ready, approve it: "
              "Actions → social → approve → the week; the episode uploads, scheduled for 11:00 Gulf.")


def report() -> None:
    tok = token()
    vids = videos(tok)
    prev = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {}
    last = prev.get("videos", {})
    ch = vids[0]["channel"]["statistics"] if vids else {}
    rows, now_stats = [], {}
    for v in vids:
        s = {k: int(v["statistics"].get(k, 0)) for k in ("viewCount", "likeCount", "commentCount")}
        now_stats[v["id"]] = s
        if v["status"].get("privacyStatus") == "private":
            continue
        before = last.get(v["id"], {}).get("viewCount", 0)
        kind = "Short" if seconds(v["contentDetails"].get("duration")) <= 60 else "Episode"
        rows.append((kind, v["snippet"]["title"][:60], s["viewCount"], s["viewCount"] - before, s["likeCount"],
                     s["commentCount"], v["id"]))
    rows.sort(key=lambda r: (r[0] != "Episode", -r[3]))
    watch = ""
    try:   # watch time needs the yt-analytics scope (re-connect YouTube to grant it)
        a = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", timeout=30,
                         headers={"Authorization": f"Bearer {tok}"},
                         params={"ids": "channel==MINE", "startDate": (NOW - timedelta(days=7)).strftime("%Y-%m-%d"),
                                 "endDate": NOW.strftime("%Y-%m-%d"),
                                 "metrics": "views,estimatedMinutesWatched,averageViewDuration,subscribersGained"})
        if a.status_code == 200 and a.json().get("rows"):
            v_, m_, d_, s_ = a.json()["rows"][0]
            watch = (f"Last 7 days: **{v_} views, {m_ / 60:.1f} hours watched, average view {d_} s, "
                     f"+{s_} subscribers**.\n\n")
        else:
            watch = "_Watch time not available: re-connect YouTube (connect → links) to grant analytics._\n\n"
    except requests.RequestException:
        pass
    lines = [f"Channel: **{ch.get('subscriberCount', '?')} subscribers**, {ch.get('viewCount', '?')} views in total.", "",
             watch + "| | Video | Views | This week | Likes | Comments |", "|---|---|---:|---:|---:|---:|"]
    lines += [f"| {k} | [{t}](https://youtu.be/{i}) | {v} | +{d} | {l} | {c} |" for k, t, v, d, l, c, i in rows]
    best = [r for r in rows if r[0] == "Short"][:1]
    if best:
        lines += ["", f"Best Short this week: **{best[0][1]}** (+{best[0][3]} views). Its topic and opening line are "
                  "worth repeating."]
    body = "\n".join(lines) + "\n"
    print(body)
    STATS.parent.mkdir(parents=True, exist_ok=True)
    STATS.write_text(json.dumps({"at": NOW.strftime("%Y-%m-%dT%H:%MZ"), "videos": now_stats}, indent=1), encoding="utf-8")
    if os.environ.get("GITHUB_REPOSITORY"):
        gh("issue", "create", "--repo", os.environ["GITHUB_REPOSITORY"], "--title",
           f"Weekly numbers {NOW:%Y-%m-%d}", "--body", body)


if __name__ == "__main__":
    {"watch-script": watch_script, "watch-publish": watch_publish, "report": report}[sys.argv[1]]()
