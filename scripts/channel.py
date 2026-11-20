"""The show's weekly health: never miss a week, and learn what works.

    python scripts/channel.py watch-script     Friday: did this week's script run succeed?
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
sys.path.insert(0, str(ROOT))   # the dashboard writer is in pipeline/publish
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
    """Friday afternoon: this morning's scheduled run (the week's script) must have succeeded."""
    repo = os.environ["GITHUB_REPOSITORY"]
    runs = json.loads(gh("run", "list", "--repo", repo, "--workflow", "weekly.yml", "--event", "schedule",
                         "--limit", "3", "--json", "conclusion,createdAt,url"))
    today = [r for r in runs if r["createdAt"][:10] == NOW.strftime("%Y-%m-%d")]
    if not today:
        alarm("This week's script did not run", "The Friday run of `weekly` never started. Run it by hand: "
              "Actions → weekly → Run workflow → phase `script`.")
    elif today[0]["conclusion"] != "success":
        alarm("This week's script failed", f"Run: {today[0]['url']} — the failure issue has the reason. "
              "Fix and re-run phase `script`, or the episode will not be ready for Sunday.")
    else:
        print("script ok:", today[0]["url"])
    until = os.environ.get("LINKEDIN_TOKEN_UNTIL", "")
    if until and datetime.strptime(until, "%Y-%m-%d").replace(tzinfo=timezone.utc) - NOW < timedelta(days=10):
        alarm("LinkedIn sign-in expires " + until, "LinkedIn tokens last 60 days. Re-connect: Actions → connect → "
              "links, click LinkedIn on the Connect accounts issue, then connect → linkedin with the address.")


def watch_publish() -> None:
    """Sunday morning: an episode (over 60 s) is scheduled to go public within the next 12 hours, or went
    public in the last 24."""
    vids = videos(token(), 15)
    soon = []
    for v in vids:
        if seconds(v["contentDetails"].get("duration")) <= 180:
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
              "Nothing on the channel goes public today. If the week's edit is ready, reply `publish` on the week's "
              "Review issue: it uploads and goes public at 17:00 Gulf (or as soon as the chapter pictures are ready).")


def retention_points(ratios: list[tuple[float, float]], length_s: float) -> str:
    """One line from YouTube's audience-retention curve [(share of the video, share still watching)]: when half
    and three quarters of the audience have gone, and the steepest fall in the first two minutes."""
    def mmss(x: float) -> str:
        t = int(round(x * length_s))
        return f"{t // 60}:{t % 60:02d}"
    if not ratios:
        return ""
    half = next((x for x, r in ratios if r < 0.5), None)
    quarter = next((x for x, r in ratios if r < 0.25), None)
    early = [(ratios[k][0], ratios[k - 1][1] - ratios[k][1]) for k in range(1, len(ratios))
             if ratios[k][0] * length_s <= 120]
    drop = max(early, key=lambda d: d[1]) if early else None
    parts = [f"half the viewers gone by {mmss(half)}" if half is not None else "over half watch to the end",
             f"three quarters by {mmss(quarter)}" if quarter is not None else ""]
    if drop and drop[1] >= 0.05:
        parts.append(f"steepest early drop at {mmss(drop[0])} (−{drop[1] * 100:.0f} points)")
    return ", ".join(p for p in parts if p)


def retention_curve(tok: str, video_id: str) -> list[tuple[float, float]]:
    try:
        a = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", timeout=30,
                         headers={"Authorization": f"Bearer {tok}"},
                         params={"ids": "channel==MINE", "startDate": "2026-01-01", "endDate": NOW.strftime("%Y-%m-%d"),
                                 "dimensions": "elapsedVideoTimeRatio", "metrics": "audienceWatchRatio",
                                 "filters": f"video=={video_id}"})
        rows = a.json().get("rows") or [] if a.status_code == 200 else []
        return [(float(x), float(r)) for x, r in rows]
    except (requests.RequestException, ValueError):
        return []


def retention(tok: str, video_id: str, length_s: float) -> str:
    return retention_points(retention_curve(tok, video_id), length_s)


def latest_runs() -> list[dict[str, str]]:
    """Each pipeline job's latest real run (comment-triggered runs that skipped are ignored), for the dashboard."""
    out = []
    for job in ("weekly", "news-watch", "social", "release", "channel", "inbox", "breaking-post", "approve"):
        try:
            runs = json.loads(gh("run", "list", "--repo", os.environ["GITHUB_REPOSITORY"], "--workflow", f"{job}.yml",
                                 "-L", "20", "--json", "conclusion,createdAt"))
        except (subprocess.SubprocessError, KeyError, ValueError, OSError):
            continue
        real = [r for r in runs if r.get("conclusion") not in ("skipped", "", None)]
        out.append({"job": job, "last_run_utc": real[0]["createdAt"][:16].replace("T", " ") if real else "",
                    "result": real[0]["conclusion"] if real else "none yet"})
    return out


def platform_lines(days: int = 7) -> list[str]:
    """Where the week's Shorts went (data/social_queue.json), with Instagram and Facebook numbers once connected.
    LinkedIn and TikTok numbers need API permissions the apps do not have; their posts are listed with links."""
    qf = ROOT / "data" / "social_queue.json"
    queue = json.loads(qf.read_text(encoding="utf-8")) if qf.exists() else []
    since = (NOW - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    done: dict[str, int] = {}
    failed: dict[str, int] = {}
    stats = []
    for e in queue:
        for plat, r in (e.get("posts") or {}).items():
            if str(r.get("at", "")) < since:
                continue
            if r.get("status") == "posted":
                done[plat] = done.get(plat, 0) + 1
                n = platform_numbers(plat, r)
                if n:
                    stats.append(f"| {plat} | {str(e.get('title', ''))[:50]} | {n} |")
            elif r.get("status") in ("failed", "skipped", "unconfirmed"):
                failed[plat] = failed.get(plat, 0) + 1
    if not done and not failed:
        return ["_No Shorts posted to other platforms this week._"]
    out = ["### Posted this week", "",
           " · ".join(f"{p}: {done.get(p, 0)}" + (f" ({failed[p]} failed)" if failed.get(p) else "")
                      for p in sorted(set(done) | set(failed)))]
    if stats:
        out += ["", "| Platform | Short | Numbers |", "|---|---|---|", *stats]
    return out


def platform_numbers(platform: str, r: dict) -> str:
    try:
        if platform == "instagram" and r.get("media_id") and os.environ.get("INSTAGRAM_TOKEN"):
            d = requests.get(f"https://graph.instagram.com/v23.0/{r['media_id']}/insights", timeout=30, params={
                "metric": "views,likes,comments,shares", "access_token": os.environ["INSTAGRAM_TOKEN"]}).json()
            vals = {m["name"]: m["values"][0]["value"] for m in d.get("data", [])}
            return ", ".join(f"{v} {k}" for k, v in vals.items())
        if platform == "facebook" and r.get("video_id") and os.environ.get("FACEBOOK_PAGE_TOKEN"):
            d = requests.get(f"https://graph.facebook.com/v23.0/{r['video_id']}", timeout=30, params={
                "fields": "views,likes.summary(true),comments.summary(true)",
                "access_token": os.environ["FACEBOOK_PAGE_TOKEN"]}).json()
            return (f"{d.get('views', '?')} views, {d.get('likes', {}).get('summary', {}).get('total_count', '?')} likes, "
                    f"{d.get('comments', {}).get('summary', {}).get('total_count', '?')} comments")
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return ""
    return ""


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
        kind = "Short" if seconds(v["contentDetails"].get("duration")) <= 180 else "Episode"
        rows.append((kind, v["snippet"]["title"][:60], s["viewCount"], s["viewCount"] - before, s["likeCount"],
                     s["commentCount"], v["id"]))
    rows.sort(key=lambda r: (r[0] != "Episode", -r[3]))
    watch, week = "", None
    try:   # watch time needs the yt-analytics scope (re-connect YouTube to grant it)
        a = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", timeout=30,
                         headers={"Authorization": f"Bearer {tok}"},
                         params={"ids": "channel==MINE", "startDate": (NOW - timedelta(days=7)).strftime("%Y-%m-%d"),
                                 "endDate": NOW.strftime("%Y-%m-%d"),
                                 "metrics": "views,estimatedMinutesWatched,averageViewDuration,subscribersGained"})
        if a.status_code == 200 and a.json().get("rows"):
            v_, m_, d_, s_ = a.json()["rows"][0]
            week = (v_, m_, d_, s_)
            watch = (f"Last 7 days: **{v_} views, {m_ / 60:.1f} hours watched, average view {d_} s, "
                     f"+{s_} subscribers**.\n\n")
        elif a.status_code == 200:
            watch = "_Watch time: no analytics rows yet for the last 7 days (YouTube's numbers lag two to three days)._\n\n"
        else:
            try:
                why = a.json().get("error", {}).get("message", "")[:200]
            except ValueError:
                why = a.text[:200]
            watch = f"_Watch time not available (HTTP {a.status_code}: {why})._\n\n"
    except requests.RequestException:
        pass
    lines = [f"Channel: **{ch.get('subscriberCount', '?')} subscribers**, {ch.get('viewCount', '?')} views in total.", "",
             watch + "| | Video | Views | This week | Likes | Comments |", "|---|---|---:|---:|---:|---:|"]
    lines += [f"| {k} | [{t}](https://youtu.be/{i}) | {v} | +{d} | {l} | {c} |" for k, t, v, d, l, c, i in rows]
    shorts = [r for r in rows if r[0] == "Short"]
    best = sorted(shorts, key=lambda r: (-r[3], -r[2]))[:1] if any(r[3] for r in shorts) else []
    if best:
        lines += ["", f"Best Short this week: **{best[0][1]}** (+{best[0][3]} views). Its topic and opening line are "
                  "worth repeating."]
    eps = [v for v in vids if v["status"].get("privacyStatus") != "private"
           and seconds(v["contentDetails"].get("duration")) > 180][:2]
    curves = [(v["snippet"]["title"][:50], retention_curve(tok, v["id"]), seconds(v["contentDetails"].get("duration")))
              for v in eps]
    ret = [(t, retention_points(c, n)) for t, c, n in curves]
    if any(r for _, r in ret):
        lines += ["", "### Where viewers leave", "", *[f"- **{t}**: {r}" for t, r in ret if r],
                  "", "_Match these times to the script's sections: a drop early in the episode usually means the "
                  "opening runs too long before the first story._"]
    lines += ["", *platform_lines()]
    body = "\n".join(lines) + "\n"
    print(body)
    try:   # the dashboard's files (pipeline/publish/dashboard.py); written on manual runs too
        from pipeline.publish import dashboard
        qf = ROOT / "data" / "social_queue.json"
        dashboard.write_files(ROOT / "data" / "dashboard", as_of=NOW.strftime("%Y-%m-%d"), channel=ch, analytics=week,
                              videos=rows, retention=[(t, dashboard.retention_numbers(c, n)) for t, c, n in curves],
                              queue=json.loads(qf.read_text(encoding="utf-8")) if qf.exists() else [],
                              runs=latest_runs())
        print("dashboard files written to data/dashboard/")
    except Exception as e:  # noqa: BLE001 — the report itself must still go out
        print(f"dashboard files not written: {e}")
    STATS.parent.mkdir(parents=True, exist_ok=True)
    if os.environ.get("GITHUB_EVENT_NAME", "schedule") != "schedule":
        print("(manual run: the weekly baseline is left as it was)")
        return
    STATS.write_text(json.dumps({"at": NOW.strftime("%Y-%m-%dT%H:%MZ"), "videos": now_stats}, indent=1), encoding="utf-8")
    if os.environ.get("GITHUB_REPOSITORY"):
        gh("issue", "create", "--repo", os.environ["GITHUB_REPOSITORY"], "--title",
           f"Weekly numbers {NOW:%Y-%m-%d}", "--body", body)


def kit_body(title: str, link: str, clip: str, short: bool, channel_url: str = "") -> str:
    """The WhatsApp kit: the same video and link for the founder's status and for the AI This Week
    WhatsApp Channel (founder 2026-11-19). WhatsApp has no API that posts to a status or a Channel."""
    clean = title.replace("#Shorts", "").strip()
    head = f"⚡ {clean}" if short else f"🆕 New episode of AI This Week: {clean}"
    channel_text = [head, "", f"▶️ {link}"] + ([f"More from the show: {channel_url}"] if short and channel_url else [])
    return "\n".join([
        f"**{clean}** is live: {link}", "",
        "### 1. Save the video", "",
        f"Open this on your phone and save it: {clip}" if clip else "No vertical clip this time: share the YouTube link instead.", "",
        "### 2. WhatsApp Channel (AI This Week)", "",
        "WhatsApp → Updates → your channel → 📎 → pick the video → paste this caption → send:", "",
        "```", *channel_text, "```", "",
        "### 3. Your status", "",
        "WhatsApp → Updates → My status → pick the same video → paste:", "",
        "```", head, link, "```", "",
        "The 10-second way for either: open the YouTube link → Share → WhatsApp."])


def status_kit() -> None:
    """Hourly: when an episode or a Short has just gone public, open a "WhatsApp kit" issue (GitHub e-mails it)
    with the vertical video to save and captions for the WhatsApp Channel and the founder's status."""
    seen_file = ROOT / "data" / "status_kits.json"
    seen = json.loads(seen_file.read_text(encoding="utf-8")) if seen_file.exists() else []
    queue_file = ROOT / "data" / "social_queue.json"
    queue = json.loads(queue_file.read_text(encoding="utf-8")) if queue_file.exists() else []
    try:
        from pipeline.config import load_settings
        channel_url = str(load_settings().get("social", {}).get("channel_url", ""))
    except Exception:  # noqa: BLE001
        channel_url = ""
    for v in videos(token(), 10):
        if v["id"] in seen or v["status"].get("privacyStatus") != "public":
            continue
        t = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
        if NOW - t > timedelta(hours=24):
            seen.append(v["id"])           # older than a day: never announce it late
            continue
        short = seconds(v["contentDetails"].get("duration")) <= 180 or "#shorts" in v["snippet"]["title"].lower()
        title, link = v["snippet"]["title"], f"https://youtu.be/{v['id']}"
        if short:   # the Short's own file, from the queue entry that posted it
            clip = next((e["url"] for e in reversed(queue)
                         if v["id"] in str(((e.get("posts") or {}).get("youtube") or {}).get("url", ""))), "")
        else:
            clip = next((e["url"] for e in reversed(queue) if e["id"].endswith("#1")), "")
        body = kit_body(title, link, clip, short, channel_url)
        gh("issue", "create", "--repo", os.environ["GITHUB_REPOSITORY"],
           "--title", f"WhatsApp kit: {title.replace('#Shorts', '').strip()[:60]}", "--body", body)
        seen.append(v["id"])
        print("whatsapp kit:", title)
    seen_file.write_text(json.dumps(seen[-50:]), encoding="utf-8")


if __name__ == "__main__":
    {"watch-script": watch_script, "watch-publish": watch_publish, "report": report,
     "status-kit": status_kit}[sys.argv[1]]()
