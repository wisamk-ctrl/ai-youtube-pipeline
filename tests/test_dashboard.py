"""The channel dashboard's data files (pipeline/publish/dashboard.py), written by the Monday report."""
import csv

from pipeline.publish import dashboard as db


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_retention_numbers_from_the_curve():
    curve = [(0.0, 1.0), (0.05, 0.62), (0.1, 0.45), (0.3, 0.3), (0.5, 0.2), (1.0, 0.05)]
    got = db.retention_numbers(curve, 600)
    assert got == {"half_gone_seconds": 60, "three_quarters_gone_seconds": 300,
                   "steepest_drop_seconds": 30, "steepest_drop_points": 38}
    assert db.retention_numbers([], 600) is None


def test_writes_every_file_with_the_dashboard_columns(tmp_path):
    db.write_files(tmp_path, as_of="2026-11-23",
                   channel={"subscriberCount": "20", "viewCount": "300"},
                   analytics=(180, 210.0, 100, 4),
                   videos=[("Episode", "Ep one", 50, 10, 4, 0, "abc"), ("Short", "Short one", 7, 7, 0, 1, "def")],
                   retention=[("Ep one", {"half_gone_seconds": 45, "three_quarters_gone_seconds": 102,
                                          "steepest_drop_seconds": 45, "steepest_drop_points": 27})],
                   queue=[{"posts": {"youtube": {"status": "posted"}, "tiktok": {"status": "queued"},
                                     "instagram": {"status": "queued"}}}],
                   runs=[{"job": "social", "last_run_utc": "2026-11-23 05:23", "result": "success"}])
    ch = read(tmp_path / "youtube_channel.csv")
    assert ch == [{"as_of": "2026-11-23", "subscribers": "20", "subscribers_gained_7d": "4", "total_views": "300",
                   "views_7d": "180", "watch_hours_7d": "3.5", "avg_view_seconds": "100"}]
    v = read(tmp_path / "youtube_videos.csv")
    assert v[0] == {"type": "Episode", "title": "Ep one", "url": "https://youtu.be/abc", "views": "50",
                    "views_7d": "10", "likes": "4", "comments": "0"}
    assert read(tmp_path / "retention.csv")[0]["episode"] == "Ep one"
    p = {r["platform"]: r for r in read(tmp_path / "platforms.csv")}
    assert p["YouTube"]["posted"] == "1" and p["YouTube"]["followers"] == "20" and p["TikTok"]["waiting"] == "1"
    assert p["Instagram"]["state"] == "blocked" and p["WhatsApp"]["posted"] == ""
    job = read(tmp_path / "pipeline.csv")[0]
    assert job["job"] == "social" and job["result"] == "success" and job["schedule"] == "hourly"


def test_missing_analytics_leaves_the_week_blank_not_zero(tmp_path):
    db.write_files(tmp_path, as_of="2026-11-23", channel={"subscriberCount": "20", "viewCount": "300"},
                   analytics=None, videos=[], retention=[], queue=[], runs=[])
    ch = read(tmp_path / "youtube_channel.csv")[0]
    assert ch["views_7d"] == "" and ch["watch_hours_7d"] == "" and ch["subscribers"] == "20"
