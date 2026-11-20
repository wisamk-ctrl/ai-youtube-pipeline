"""The channel dashboard's data files (founder 2026-11-20): data/dashboard/*.csv, written by the Monday report
(scripts/channel.py report) from the numbers it already fetched, and uploaded to the dashboard artifact by a weekly
routine. Every figure is computed here, in code; the routine only copies the files."""
from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable

# What the app cannot read about each account, kept by hand (update when an account's state changes).
ACCOUNTS = [
    ("YouTube", "youtube", "@AIThisWeekME", "working", "Episodes and Shorts post automatically"),
    ("TikTok", "tiktok", "@aithisweek", "manual", "Shorts arrive in your TikTok drafts: paste the caption from the issue and tap Post"),
    ("LinkedIn", "linkedin", "Wissam Kishek (profile)", "working", "Follower count not available to the app"),
    ("Instagram", "instagram", "@aithisweekme", "blocked", "Needs the Meta developer app (phone check)"),
    ("Facebook", "facebook", "AI This Week (Page)", "blocked", "Needs the Meta developer app (phone check)"),
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
    """'Breaking' for a same-day breaking Short, 'Episode clip' for one cut from an episode, '' when unknown."""
    for e in queue:
        url = str((e.get("posts") or {}).get("youtube", {}).get("url") or "")
        if url.rstrip("/").endswith(video_id):
            return "Breaking" if "-brk-" in str(e.get("week", "")) else "Episode clip"
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
              posted_weeks: set[str] | None = None) -> list[dict[str, str]]:
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
             for name, _, _, state, note in ACCOUNTS if state == "blocked"]
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
                traffic: list[tuple] | None = None, needs: list[dict[str, str]] | None = None) -> None:
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
    _write(out / "youtube_videos.csv", ["type", "origin", "title", "url", "views", "views_7d", "likes", "comments"],
           [{"type": k, "origin": short_origin(i, queue) if k == "Short" else "", "title": full(i, t),
             "url": f"https://youtu.be/{i}", "views": v, "views_7d": d, "likes": l, "comments": c}
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
    _write(out / "platforms.csv", ["platform", "account", "state", "followers", "posted", "waiting", "note"],
           [{"platform": name, "account": acct, "state": state,
             "followers": channel.get("subscriberCount") if key == "youtube" else None,
             "posted": counts.get(key, {}).get("posted", 0) if key else None,
             "waiting": counts.get(key, {}).get("waiting", 0) if key else None, "note": note}
            for name, key, acct, state, note in ACCOUNTS])
    _write(out / "pipeline.csv", ["job", "what_it_does", "schedule", "last_run_utc", "result", "note"],
           [{"job": r["job"], "what_it_does": WHAT.get(r["job"], ""), "schedule": SCHEDULES.get(r["job"], ""),
             "last_run_utc": r.get("last_run_utc", ""), "result": r.get("result", ""), "note": r.get("note", "")}
            for r in runs])
