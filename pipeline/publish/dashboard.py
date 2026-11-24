"""The channel dashboard's data files (founder 2026-11-20): data/dashboard/*.csv, written every 3 hours by
scripts/channel.py (mode `dashboard`, and the Monday report) and read live from GitHub by the dashboard page
(founder 2026-11-23). Every figure is computed here, in code; the page only draws it."""
from __future__ import annotations

import csv
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

# What the app cannot read about each account, kept by hand (update when an account's state changes).
ACCOUNTS = [
    ("YouTube", "youtube", "@AIThisWeekME", "working", "Episodes and Shorts post automatically"),
    ("TikTok", "tiktok", "@aithisweek", "manual", "Shorts arrive in your TikTok drafts: paste the caption from the issue and tap Post"),
    ("LinkedIn", "linkedin", "Wissam Kishek (profile)", "working", "Follower count not available to the app"),
    ("Instagram", "instagram", "@aithisweekme", "working", "Reels post automatically"),
    ("Facebook", "facebook", "AI This Week (Page)", "working", "Reels post automatically"),
    ("WhatsApp", None, "AI This Week (Channel)", "manual", "No API: hourly kit for you to post"),
]
SCHEDULES = {"weekly": "Fri 06:00 + on demand", "news-watch": "every 2 h", "social": "hourly", "release": "every 20 min",
             "channel": "hourly + Mon", "inbox": "daily 05:13", "breaking-post": "on your post reply",
             "approve": "on your approve reply"}
WHAT = {"weekly": "Script run and renders", "news-watch": "Spots breaking stories", "social": "Posts queued Shorts",
        "release": "Makes episodes public", "channel": "Numbers and WhatsApp kit", "inbox": "Daily comment inbox",
        "breaking-post": "Posts an approved breaking Short", "approve": "Starts the weekly chain"}


TRAFFIC = {"YT_SEARCH": "YouTube search", "RELATED_VIDEO": "Suggested videos", "SHORTS": "Shorts feed",
           "BROWSE": "Browse / home", "EXT_URL": "External links", "NO_LINK_OTHER": "Direct or unknown",
           "SUBSCRIBER": "Subscriptions", "PLAYLIST": "Playlists", "CHANNEL": "Channel pages", "YT_CHANNEL": "Channel pages", "NOTIFICATION": "Notifications",
           "END_SCREEN": "End screens", "YT_OTHER_PAGE": "Other YouTube pages", "HASHTAGS": "Hashtags"}
HISTORY_COLS = ["week", "as_of", "subscribers", "total_views", "views_7d", "watch_hours_7d", "watch_hours_365d",
                "avg_view_seconds"]


PLATS = ("youtube", "instagram", "facebook", "linkedin", "tiktok")
STAT_COLS = ["instagram_views", "instagram_likes", "facebook_views", "facebook_likes"]
POST_COLS = ["date", "title", "kind", *PLATS, *STAT_COLS]

# YouTube Partner Program entry bars (YouTube Help "YouTube Partner Program overview & eligibility", checked
# 2026-11-24). Either watch route counts: long-form hours in 12 months, or Shorts views in 90 days.
YPP = [("Fan funding", 500, 3000, 3_000_000), ("Ad revenue", 1000, 4000, 10_000_000)]
MONEY_COLS = ["tier", "metric", "current", "target", "window", "per_day", "needed_per_day", "eta"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
EPISODE_COLS = ["week", "step", "status", "date", "link"]
ALERT_COLS = ["level", "message", "link"]


def live_states(queue: list[dict[str, Any]], days: int = 14) -> dict[str, tuple[str, str]]:
    """Each platform's state from what really happened lately, not from a note typed once (2026-11-23: Instagram
    and Facebook showed "blocked" for days while posting fine)."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: dict[str, tuple[str, str]] = {}
    for p in PLATS:
        rs = [r for e in queue for k, r in (e.get("posts") or {}).items() if k == p]
        recent = [r for r in rs if str(r.get("at", "")) >= since]
        ok = [r for r in recent if r.get("status") == "posted"]
        bad = [r for r in recent if r.get("status") in ("failed", "skipped")]
        if p == "tiktok" and ok:
            out[p] = ("manual", f"{len(ok)} sent to your TikTok drafts in {days} days: post them from the app")
        elif ok:
            out[p] = ("working", f"{len(ok)} posted in the last {days} days" + (f", {len(bad)} failed" if bad else ""))
        elif bad:
            out[p] = ("failing", f"{len(bad)} failed in the last {days} days: {str(bad[-1].get('error', ''))[:80]}")
    return out


def post_rows(queue: list[dict[str, Any]], limit: int = 40,
              stats: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """The latest clips with each platform's link (or what happened), newest first. stats: views and likes by
    Instagram media id or Facebook video id, where the platform gave them (blank otherwise, never zero)."""
    stats = stats or {}
    rows = []
    for e in queue:
        posts = e.get("posts") or {}
        at = max((str(r.get("at", "")) for r in posts.values()), default="") or str(e.get("due", ""))
        if not any(r.get("status") == "posted" for r in posts.values()):
            continue
        row = {"date": at[:10], "title": re.sub(r"\s*#Shorts\s*$", "", str(e.get("title") or e.get("file", ""))),
               "kind": "breaking" if "-brk-" in str(e.get("week", "")) else "weekly"}
        for p in PLATS:
            r = posts.get(p) or {}
            url = str(r.get("url", ""))
            row[p] = url if url.startswith("https://") else ("drafts" if p == "tiktok" and r.get("status") == "posted"
                                                               else (r.get("status") or ""))
        for p, key in (("instagram", "media_id"), ("facebook", "video_id")):
            got = stats.get(str((posts.get(p) or {}).get(key) or ""), {})
            row[f"{p}_views"], row[f"{p}_likes"] = got.get("views"), got.get("likes")
        rows.append(row)
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows[:limit]


def monetisation_rows(*, subscribers: float | None, hours_365: float | None, shorts_90: float | None,
                      subs_per_day: float | None, hours_per_day: float | None, shorts_per_day: float | None,
                      today: str) -> list[dict[str, Any]]:
    """Where the channel stands against each YouTube Partner Program bar, with the pace of the last 28 days and the
    date it would be reached at that pace. The Shorts route is a rolling 90 days, so it is reached only when the
    daily pace itself is high enough: then the date is when the 90-day total would get there."""
    d0 = date.fromisoformat(today)
    rows = []
    for tier, subs_t, hours_t, shorts_t in YPP:
        for metric, cur, target, window, pace, rolling in (
                ("Subscribers", subscribers, subs_t, "now", subs_per_day, False),
                ("Watch hours (long videos)", hours_365, hours_t, "12 months", hours_per_day, False),
                ("Shorts views", shorts_90, shorts_t, "90 days", shorts_per_day, True)):
            needed = round(target / 90) if rolling else None
            if cur is None:
                eta = ""
            elif cur >= target:
                eta = "reached"
            elif not pace or pace <= 0 or (rolling and pace < target / 90):
                eta = "not at this pace"
            else:
                eta = (d0 + timedelta(days=-(-(target - cur) // pace))).isoformat()
            rows.append({"tier": tier, "metric": metric, "current": cur, "target": target, "window": window,
                         "per_day": None if pace is None else round(pace, 2), "needed_per_day": needed, "eta": eta})
    return rows


def weekday_rows(days: list[tuple]) -> list[dict[str, Any]]:
    """Average views and hours watched on each weekday, from YouTube's daily rows (date, views, minutes)."""
    acc: dict[int, list[float]] = {}
    for d, views, minutes in days:
        a = acc.setdefault(date.fromisoformat(str(d)).weekday(), [0, 0.0, 0.0])
        a[0] += 1
        a[1] += float(views or 0)
        a[2] += float(minutes or 0)
    return [{"weekday": WEEKDAYS[k], "days": n, "avg_views": round(v / n, 1), "avg_watch_hours": round(m / n / 60, 2)}
            for k, (n, v, m) in sorted(acc.items())]


def episode_steps(week: str, issue: dict[str, Any] | None, owner: str, releases: list[dict[str, Any]],
                  shorts_posted: int) -> list[dict[str, Any]]:
    """The week's episode from script to public: each step done (with its date), next, or waiting. Signals: the
    Review issue and the founder's replies on it, the "ready to check" comment, and data/releases.json."""
    comments = (issue or {}).get("comments") or []
    def first(test):   # noqa: E306
        return next((str(c.get("createdAt", ""))[:10] for c in comments if test(c)), "")
    mine = lambda c, word: (c.get("author") or {}).get("login") == owner and \
        str(c.get("body", "")).strip().lower().startswith(word)   # noqa: E731
    rel = next((r for r in releases if str(r.get("week", "")).removesuffix("-en") == week), None)
    done = [("Script ready for review", str((issue or {}).get("createdAt", ""))[:10] if issue else ""),
            ("Script approved", first(lambda c: mine(c, "approve"))),
            ("Episode and Shorts rendered", first(lambda c: "Episode ready to check" in str(c.get("body", "")))),
            ("Publish approved", first(lambda c: mine(c, "publish"))),
            ("Scheduled on YouTube", str((rel or {}).get("release_at", ""))[:10]),
            ("Public", str((rel or {}).get("at", ""))[:10] if (rel or {}).get("status") == "public" else "")]
    rows, nxt = [], False
    for step, when in done:
        status = "done" if when else ("waiting" if nxt else "next")
        nxt = nxt or not when
        rows.append({"week": week, "step": step, "status": status, "date": when,
                     "link": (issue or {}).get("url", "") if step != "Public" or not rel
                     else f"https://youtu.be/{rel.get('video_id', '')}"})
    rows.append({"week": week, "step": f"Shorts posted ({shorts_posted})",
                 "status": "done" if shorts_posted else "waiting", "date": "", "link": ""})
    return rows


def alert_rows(runs: list[dict[str, str]], live: dict[str, tuple[str, str]], analytics_ok: bool,
               repo_url: str = "") -> list[dict[str, str]]:
    """What is broken right now, for the banner at the top: failed jobs, failing platforms, missing YouTube numbers."""
    out = [{"level": "bad", "message": f"The {r['job']} job failed on its last run ({r.get('last_run_utc', '')} UTC)",
            "link": f"{repo_url}/actions/workflows/{r['job']}.yml" if repo_url else ""}
           for r in runs if r.get("result") in ("failure", "timed_out", "startup_failure")]
    out += [{"level": "bad", "message": f"{p.title()}: {note}", "link": ""}
            for p, (state, note) in live.items() if state == "failing"]
    if not analytics_ok:
        out.append({"level": "warn", "message": "YouTube Analytics gave no numbers for the last 7 days: the YouTube "
                    "connection may need its analytics permission again", "link": ""})
    return out


def append_history(path: Path, row: dict[str, Any]) -> None:
    """One row per ISO week: a later run in the same week replaces that week's row."""
    y, w, _ = date.fromisoformat(str(row["as_of"])).isocalendar()
    row = {**row, "week": f"{y}-W{w:02d}"}
    rows = []
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r.get("week") != row["week"]]
    rows.append(row)
    rows.sort(key=lambda r: r["week"])
    _write(path, HISTORY_COLS, rows)


def short_origin(video_id: str, queue: list[dict[str, Any]]) -> str:
    """'Breaking' for a same-day breaking Short, 'Explainer' for one from the ranking, 'Episode clip' for one cut from an episode, '' when unknown."""
    for e in queue:
        url = str((e.get("posts") or {}).get("youtube", {}).get("url") or "")
        if url.rstrip("/").endswith(video_id):
            week = str(e.get("week", ""))
            return "Breaking" if "-brk-" in week else "Explainer" if "-exp-" in week else "Episode clip"
    return ""


def chapters(description: str) -> list[tuple[int, str]]:
    """YouTube chapter lines in a description ("01:50 Title" or "1:02:03 Title") as (seconds, title)."""
    out = []
    for m in re.finditer(r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\s+(.+?)\s*$", description or "", re.M):
        h, mm, ss, title = m.groups()
        out.append((int(h or 0) * 3600 + int(mm) * 60 + int(ss), title))
    return out


def curve_rows(episode: str, curve: list[tuple[float, float]], length_s: float) -> list[dict[str, Any]]:
    return [{"episode": episode, "second": int(round(x * length_s)), "watching_pct": round(r * 100, 1)} for x, r in curve]


def needs_you(issues: list[dict[str, Any]], breaking_comments: list[dict[str, Any]], *, linkedin_until: str,
              today: str, breaking_url: str, now: str | None = None,
              published_weeks: set[str] | None = None, breaking_titles: dict[str, list[str]] | None = None,
              posted_weeks: set[str] | None = None,
              live: dict[str, tuple[str, str]] | None = None) -> list[dict[str, str]]:
    """What waits on the founder: a Review issue from the last 7 days, open failure issues, breaking Shorts ready in
    the last 36 hours but not posted (older drafts are stale news), a LinkedIn token close to expiry, and blocked
    accounts. Open Review issues from earlier weeks are finished work, not waiting."""
    from datetime import datetime, timedelta
    ts = lambda s: datetime.fromisoformat(str(s).replace("Z", "+00:00"))   # noqa: E731
    at = ts(now) if now else ts(f"{today}T23:59:59+00:00")
    rows = []
    for i in issues:
        t = i.get("title", "")
        kind = "Approve" if t.startswith("Review:") else "Fix" if t.startswith(("Run failed", "Show at risk")) else ""
        if kind == "Approve" and at - ts(i.get("createdAt") or "1970-01-01T00:00:00Z") > timedelta(days=7):
            continue
        wk = re.search(r"\((\d{4}-W\d{2})[^)]*\)\s*$", t)
        if kind == "Approve" and wk and any(p.startswith(wk.group(1)) for p in (published_weeks or ())):
            continue   # that week already reached the posting record: its review is finished
        if kind:
            rows.append({"kind": kind, "item": t, "since": str(i.get("createdAt", ""))[:10], "link": i.get("url", "")})
    ready: dict[str, str] = {}
    for c in breaking_comments:
        body = c.get("body", "")
        if (m := re.search(r"Ready to check: `([^`]+)`", body)) and \
                at - ts(c.get("createdAt") or "1970-01-01T00:00:00Z") <= timedelta(hours=36):
            ready[m.group(1)] = str(c.get("createdAt", ""))[:10]
        if m := re.search(r"Posted: `([^`]+)`", body):
            ready.pop(m.group(1), None)
    from pipeline.story_match import is_repeat
    titles = breaking_titles or {}
    posted = [h for w in (posted_weeks or ()) if "-brk-" in w for h in titles.get(w, [])]
    rows += [{"kind": "Your call", "item": f"Breaking Short {w}: post it or let it expire", "since": d,
              "link": breaking_url}
             for w, d in sorted(ready.items(), key=lambda x: x[1], reverse=True)
             if not (posted and is_repeat(titles.get(w, []), posted))]   # a story already posted is not waiting
    if linkedin_until:
        try:
            left = (date.fromisoformat(linkedin_until[:10]) - date.fromisoformat(today)).days
            if left <= 21:
                rows.append({"kind": "Renew", "item": f"LinkedIn token expires in {left} days", "since": today,
                             "link": "https://www.linkedin.com/developers/tools/oauth/token-generator"})
        except ValueError:
            pass
    rows += [{"kind": "Unblock", "item": f"{name}: {note}", "since": "", "link": ""}
             for name, key, _, state, note in ACCOUNTS
             if state == "blocked" and (live or {}).get(key or "", ("blocked",))[0] != "working"]
    return rows


def retention_numbers(curve: list[tuple[float, float]], length_s: float) -> dict[str, int] | None:
    """The same reading as channel.retention_points, as numbers: seconds until half and three quarters of the
    audience have gone, and the steepest fall in the first two minutes (where, and how many points)."""
    if not curve:
        return None
    half = next((x for x, r in curve if r < 0.5), None)
    quarter = next((x for x, r in curve if r < 0.25), None)
    early = [(curve[k][0], curve[k - 1][1] - curve[k][1]) for k in range(1, len(curve)) if curve[k][0] * length_s <= 120]
    drop = max(early, key=lambda d: d[1]) if early else None
    sec = lambda x: int(round(x * length_s)) if x is not None else ""   # noqa: E731
    return {"half_gone_seconds": sec(half), "three_quarters_gone_seconds": sec(quarter),
            "steepest_drop_seconds": sec(drop[0]) if drop else "",
            "steepest_drop_points": int(round(drop[1] * 100)) if drop else ""}


def _write(path: Path, cols: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in cols})


def write_files(out: Path, *, as_of: str, channel: dict[str, Any], analytics: tuple | None,
                videos: list[tuple], retention: list[tuple[str, dict[str, int] | None]],
                queue: list[dict[str, Any]], runs: list[dict[str, str]], titles: dict[str, str] | None = None,
                hours_365: float | None = None, curves: list[tuple] | None = None,
                chapter_rows: list[tuple[str, int, str]] | None = None, countries: list[tuple] | None = None,
                traffic: list[tuple] | None = None, needs: list[dict[str, str]] | None = None,
                video_subs: dict[str, int] | None = None, post_stats: dict[str, dict[str, Any]] | None = None,
                money: list[dict[str, Any]] | None = None, weekdays: list[dict[str, Any]] | None = None,
                episode: list[dict[str, Any]] | None = None, alerts: list[dict[str, str]] | None = None) -> None:
    """analytics: (views, minutes watched, average view s, subscribers gained) for the last 7 days, or None when
    YouTube gave none (left blank, never zero). videos: the report's rows (kind, title, views, change, likes,
    comments, id). runs: {job, last_run_utc, result} per job."""
    out.mkdir(parents=True, exist_ok=True)
    views7, minutes, avg, gained = analytics if analytics else (None, None, None, None)
    hours = lambda m: None if m is None else f"{float(m) / 60:.1f}"   # noqa: E731
    ch_row = {"as_of": as_of, "subscribers": channel.get("subscriberCount"), "subscribers_gained_7d": gained,
              "total_views": channel.get("viewCount"), "views_7d": views7, "watch_hours_7d": hours(minutes),
              "watch_hours_365d": None if hours_365 is None else f"{hours_365:.1f}", "avg_view_seconds": avg}
    _write(out / "youtube_channel.csv", ["as_of", "subscribers", "subscribers_gained_7d", "total_views", "views_7d",
                                         "watch_hours_7d", "watch_hours_365d", "avg_view_seconds"], [ch_row])
    append_history(out / "history.csv", {k: ch_row[k] for k in HISTORY_COLS if k != "week"})
    titles = titles or {}
    full = lambda i, t: re.sub(r"\s*#Shorts\s*$", "", titles.get(i, t))   # noqa: E731
    subs = video_subs if video_subs is not None else {}
    _write(out / "youtube_videos.csv", ["type", "origin", "title", "url", "views", "views_7d", "likes", "comments",
                                        "subscribers_gained"],
           [{"type": k, "origin": short_origin(i, queue) if k == "Short" else "", "title": full(i, t),
             "url": f"https://youtu.be/{i}", "views": v, "views_7d": d, "likes": l, "comments": c,
             "subscribers_gained": subs.get(i, 0 if video_subs is not None else None)}
            for k, t, v, d, l, c, i in videos])
    _write(out / "retention_curve.csv", ["episode", "second", "watching_pct"],
           [r for t, c, n in (curves or []) for r in curve_rows(t, c, n)])
    _write(out / "chapters.csv", ["episode", "second", "chapter"],
           [{"episode": t, "second": s, "chapter": c} for t, s, c in (chapter_rows or [])])
    _write(out / "countries.csv", ["country", "views", "watch_hours"],
           [{"country": c, "views": v, "watch_hours": hours(m)} for c, v, m in (countries or [])])
    _write(out / "traffic.csv", ["source", "views", "watch_hours"],
           [{"source": TRAFFIC.get(s, s.replace("_", " ").title()), "views": v, "watch_hours": hours(m)}
            for s, v, m in (traffic or [])])
    _write(out / "needs_you.csv", ["kind", "item", "since", "link"], needs or [])
    _write(out / "retention.csv", ["episode", "half_gone_seconds", "three_quarters_gone_seconds",
                                   "steepest_drop_seconds", "steepest_drop_points"],
           [{"episode": t, **n} for t, n in retention if n])
    counts: dict[str, dict[str, int]] = {}
    for e in queue:
        for plat, r in (e.get("posts") or {}).items():
            c = counts.setdefault(plat, {"posted": 0, "waiting": 0})
            if r.get("status") == "posted":
                c["posted"] += 1
            elif r.get("status") in ("queued", "failed"):
                c["waiting"] += 1
    live = live_states(queue)
    _write(out / "platforms.csv", ["platform", "account", "state", "followers", "posted", "waiting", "note"],
           [{"platform": name, "account": acct, "state": live.get(key, (state, note))[0],
             "followers": channel.get("subscriberCount") if key == "youtube" else None,
             "posted": counts.get(key, {}).get("posted", 0) if key else None,
             "waiting": counts.get(key, {}).get("waiting", 0) if key else None,
             "note": live.get(key, (state, note))[1]}
            for name, key, acct, state, note in ACCOUNTS])
    _write(out / "posts.csv", POST_COLS, post_rows(queue, stats=post_stats))
    _write(out / "monetisation.csv", MONEY_COLS, money or [])
    _write(out / "weekdays.csv", ["weekday", "days", "avg_views", "avg_watch_hours"], weekdays or [])
    _write(out / "episode.csv", EPISODE_COLS, episode or [])
    _write(out / "alerts.csv", ALERT_COLS, alerts or [])
    _write(out / "pipeline.csv", ["job", "what_it_does", "schedule", "last_run_utc", "result", "note"],
           [{"job": r["job"], "what_it_does": WHAT.get(r["job"], ""), "schedule": SCHEDULES.get(r["job"], ""),
             "last_run_utc": r.get("last_run_utc", ""), "result": r.get("result", ""), "note": r.get("note", "")}
            for r in runs])
