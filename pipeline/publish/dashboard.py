"""The channel dashboard's data files (founder 2026-11-20): data/dashboard/*.csv, written by the Monday report
(scripts/channel.py report) from the numbers it already fetched, and uploaded to the dashboard artifact by a weekly
routine. Every figure is computed here, in code; the routine only copies the files."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

# What the app cannot read about each account, kept by hand (update when an account's state changes).
ACCOUNTS = [
    ("YouTube", "youtube", "@AIThisWeekME", "working", "Episodes and Shorts post automatically"),
    ("TikTok", "tiktok", "@aithisweek", "working", "Public account since 19 Nov; app posts may still land private"),
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
                queue: list[dict[str, Any]], runs: list[dict[str, str]]) -> None:
    """analytics: (views, minutes watched, average view s, subscribers gained) for the last 7 days, or None when
    YouTube gave none (left blank, never zero). videos: the report's rows (kind, title, views, change, likes,
    comments, id). runs: {job, last_run_utc, result} per job."""
    out.mkdir(parents=True, exist_ok=True)
    views7, minutes, avg, gained = analytics if analytics else (None, None, None, None)
    _write(out / "youtube_channel.csv",
           ["as_of", "subscribers", "subscribers_gained_7d", "total_views", "views_7d", "watch_hours_7d", "avg_view_seconds"],
           [{"as_of": as_of, "subscribers": channel.get("subscriberCount"), "subscribers_gained_7d": gained,
             "total_views": channel.get("viewCount"), "views_7d": views7,
             "watch_hours_7d": None if minutes is None else f"{minutes / 60:.1f}", "avg_view_seconds": avg}])
    _write(out / "youtube_videos.csv", ["type", "title", "url", "views", "views_7d", "likes", "comments"],
           [{"type": k, "title": t, "url": f"https://youtu.be/{i}", "views": v, "views_7d": d, "likes": l,
             "comments": c} for k, t, v, d, l, c, i in videos])
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
