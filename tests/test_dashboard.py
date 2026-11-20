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
                   "views_7d": "180", "watch_hours_7d": "3.5", "watch_hours_365d": "",
                   "avg_view_seconds": "100"}]
    v = read(tmp_path / "youtube_videos.csv")
    assert v[0] == {"type": "Episode", "origin": "", "title": "Ep one", "url": "https://youtu.be/abc", "views": "50",
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


# ── Enhancements (founder 2026-11-20: "all of them") ─────────────────────────
def test_history_keeps_one_row_per_week(tmp_path):
    f = tmp_path / "history.csv"
    db.append_history(f, {"as_of": "2026-11-23", "subscribers": 20, "watch_hours_7d": "3.5"})
    db.append_history(f, {"as_of": "2026-11-24", "subscribers": 21, "watch_hours_7d": "3.6"})   # same ISO week
    db.append_history(f, {"as_of": "2026-11-30", "subscribers": 25, "watch_hours_7d": "4.0"})
    rows = read(f)
    assert [(r["week"], r["subscribers"]) for r in rows] == [("2026-W48", "21"), ("2026-W49", "25")]


def test_short_origin_from_the_posting_record():
    queue = [{"week": "2026-11-18-brk-outages-en", "posts": {"youtube": {"url": "https://youtube.com/shorts/qTj"}}},
             {"week": "2026-W46-en", "posts": {"youtube": {"url": "https://youtube.com/shorts/ObU"}}}]
    assert db.short_origin("qTj", queue) == "Breaking"
    assert db.short_origin("ObU", queue) == "Episode clip"
    assert db.short_origin("zzz", queue) == ""


def test_chapters_from_a_description():
    d = "Intro text\n\nIn this episode:\n00:00 Opening\n0:20 Welcome\n01:50 Anthropic's IPO\n1:02:03 Long\nnot a chapter"
    assert db.chapters(d) == [(0, "Opening"), (20, "Welcome"), (110, "Anthropic's IPO"), (3723, "Long")]


def test_curve_rows_in_seconds_and_percent():
    assert db.curve_rows("Ep", [(0.0, 1.0), (0.5, 0.42)], 600) == [
        {"episode": "Ep", "second": 0, "watching_pct": 100.0}, {"episode": "Ep", "second": 300, "watching_pct": 42.0}]


def test_needs_you_lists_what_waits_on_the_founder():
    issues = [{"number": 46, "title": "Review: episode (2026-W47)", "url": "u46", "createdAt": "2026-11-20T06:30:00Z"},
              {"number": 47, "title": "Run failed: render job (x)", "url": "u47", "createdAt": "2026-11-20T03:04:00Z"},
              {"number": 45, "title": "Weekly numbers 2026-11-19", "url": "u45", "createdAt": "2026-11-19T13:00:00Z"}]
    breaking = [{"body": "**Ready to check: `2026-11-20-brk-a-en`**", "createdAt": "2026-11-20T01:00:00Z"},
                {"body": "**Ready to check: `2026-11-19-brk-b-en`**", "createdAt": "2026-11-19T01:00:00Z"},
                {"body": "**Posted: `2026-11-19-brk-b-en`**\n\n- youtube: posted", "createdAt": "2026-11-19T02:00:00Z"}]
    rows = db.needs_you(issues, breaking, linkedin_until="2026-12-01", today="2026-11-20", breaking_url="ub")
    kinds = [(r["kind"], r["item"]) for r in rows]
    assert ("Approve", "Review: episode (2026-W47)") in kinds
    assert ("Fix", "Run failed: render job (x)") in kinds
    assert ("Your call", "Breaking Short 2026-11-20-brk-a-en: post it or let it expire") in kinds
    assert not any("brk-b" in i for _, i in kinds) and not any("Weekly numbers" in i for _, i in kinds)
    assert ("Renew", "LinkedIn token expires in 11 days") in kinds
    assert any(k == "Unblock" and "Instagram" in i for k, i in kinds)


def test_linkedin_token_far_off_is_not_listed():
    rows = db.needs_you([], [], linkedin_until="2027-03-01", today="2026-11-20", breaking_url="ub")
    assert not any(r["kind"] == "Renew" for r in rows)


def test_write_files_adds_the_new_files(tmp_path):
    db.write_files(tmp_path, as_of="2026-11-23", channel={"subscriberCount": "20", "viewCount": "300"},
                   analytics=(180, 210.0, 100, 4), videos=[("Short", "S", 7, 7, 0, 1, "qTj")], retention=[],
                   queue=[{"week": "2026-11-18-brk-outages-en", "posts": {"youtube": {"url": "https://youtube.com/shorts/qTj"}}}],
                   runs=[], titles={"qTj": "Six US Outages in Six Days #Shorts"}, hours_365=12.5,
                   curves=[("Ep", [(0.0, 1.0)], 600)], chapter_rows=[("Ep", 0, "Opening")],
                   countries=[("AE", 40, 90.0)], traffic=[("YT_SEARCH", 10, 20.0)],
                   needs=[{"kind": "Fix", "item": "x", "since": "2026-11-20", "link": "u"}])
    v = read(tmp_path / "youtube_videos.csv")[0]
    assert v["title"] == "Six US Outages in Six Days" and v["origin"] == "Breaking"
    assert read(tmp_path / "youtube_channel.csv")[0]["watch_hours_365d"] == "12.5"
    assert read(tmp_path / "retention_curve.csv")[0] == {"episode": "Ep", "second": "0", "watching_pct": "100.0"}
    assert read(tmp_path / "chapters.csv")[0] == {"episode": "Ep", "second": "0", "chapter": "Opening"}
    assert read(tmp_path / "countries.csv")[0] == {"country": "AE", "views": "40", "watch_hours": "1.5"}
    assert read(tmp_path / "traffic.csv")[0] == {"source": "YouTube search", "views": "10", "watch_hours": "0.3"}
    assert read(tmp_path / "needs_you.csv")[0]["kind"] == "Fix"
    assert read(tmp_path / "history.csv")[0]["week"] == "2026-W48"


def test_needs_you_skips_old_reviews_and_stale_breaking_drafts():
    """2026-11-20 first real run: 8 finished Review issues (W41–W46) and 8 superseded breaking drafts were listed."""
    issues = [{"title": "Review: old (2026-W45)", "url": "u", "createdAt": "2026-11-07T06:00:00Z"},
              {"title": "Review: this week (2026-W47)", "url": "u", "createdAt": "2026-11-20T06:30:00Z"}]
    comments = [{"body": "**Ready to check: `2026-11-18-brk-old-en`**", "createdAt": "2026-11-18T09:00:00Z"},
                {"body": "**Ready to check: `2026-11-20-brk-new-en`**", "createdAt": "2026-11-20T01:00:00Z"}]
    rows = db.needs_you(issues, comments, linkedin_until="", today="2026-11-20", breaking_url="b",
                        now="2026-11-20T08:00:00Z")
    items = [r["item"] for r in rows]
    assert "Review: this week (2026-W47)" in items and "Review: old (2026-W45)" not in items
    assert any("brk-new" in i for i in items) and not any("brk-old" in i for i in items)
    assert db.TRAFFIC["YT_CHANNEL"] == "Channel pages"


def test_a_review_whose_week_already_went_out_is_not_waiting():
    """2026-11-20: the W46 Review issue was still open although W46-en had been published."""
    issues = [{"title": "Review: done (2026-W46)", "url": "u", "createdAt": "2026-11-14T06:00:00Z"},
              {"title": "Review: new (2026-W47)", "url": "u", "createdAt": "2026-11-20T06:30:00Z"}]
    rows = db.needs_you(issues, [], linkedin_until="", today="2026-11-20", breaking_url="b",
                        now="2026-11-20T08:00:00Z", published_weeks={"2026-W46-en", "2026-W45-en"})
    items = [r["item"] for r in rows]
    assert "Review: new (2026-W47)" in items and "Review: done (2026-W46)" not in items



def test_a_breaking_draft_that_repeats_a_posted_story_is_hidden():
    """2026-11-20: the outage had been posted on 18 Nov, yet five later outage drafts were listed as waiting."""
    comments = [{"body": "**Ready to check: `2026-11-20-brk-ms-outage-en`**", "createdAt": "2026-11-20T04:00:00Z"},
                {"body": "**Ready to check: `2026-11-20-brk-anthropic-ipo-en`**", "createdAt": "2026-11-20T03:00:00Z"}]
    titles = {"2026-11-20-brk-ms-outage-en": ["Microsoft outage brings enterprise resilience gaps to light"],
              "2026-11-20-brk-anthropic-ipo-en": ["Why Anthropic Stock Is Up (and Down) Today"],
              "2026-11-18-brk-outages-en": ["Microsoft reveals hidden bug behind global Microsoft 365 outage"]}
    rows = db.needs_you([], comments, linkedin_until="", today="2026-11-20", breaking_url="b", now="2026-11-20T08:00:00Z",
                        breaking_titles=titles, posted_weeks={"2026-11-18-brk-outages-en"})
    items = [r["item"] for r in rows]
    assert not any("ms-outage" in i for i in items) and any("anthropic-ipo" in i for i in items)
