"""The episode's announcement (pipeline/publish/announce.py): never twice on one channel, never silently missing."""
import json

from pipeline.publish import announce as an


def boom():
    raise RuntimeError("HTTP 500")


def test_posts_each_channel_once_and_records_it():
    calls = []
    posters = {"linkedin": lambda: calls.append("li") or "urn:li:1", "facebook": lambda: calls.append("fb") or "99"}
    done, problems = an.announce("text", {}, posters)
    assert done == {"linkedin": "urn:li:1", "facebook": "99"} and problems == [] and calls == ["li", "fb"]


def test_a_channel_already_announced_is_never_posted_again():
    calls = []
    done, problems = an.announce("text", {"linkedin": "urn:li:1"},
                                 {"linkedin": lambda: calls.append("li"), "facebook": lambda: "99"})
    assert calls == [] and done == {"linkedin": "urn:li:1", "facebook": "99"} and problems == []


def test_one_failure_is_reported_and_does_not_stop_the_other_channel():
    done, problems = an.announce("text", {}, {"linkedin": boom, "facebook": lambda: "99"})
    assert done == {"facebook": "99"}
    assert len(problems) == 1 and "linkedin" in problems[0] and "HTTP 500" in problems[0]


def test_missing_text_is_a_problem_not_a_quiet_skip():
    calls = []
    done, problems = an.announce("  ", {}, {"linkedin": lambda: calls.append("li")})
    assert calls == [] and done == {} and "linkedin_post_en" in problems[0] and "linkedin" in problems[0]
    assert an.announce("", {"linkedin": "x"}, {"linkedin": boom}) == ({"linkedin": "x"}, [])   # nothing left to post


def test_the_record_survives_on_disk_per_week(tmp_path):
    f = tmp_path / "announced.json"
    assert an.load(f, "2026-W47-en") == {}
    an.save(f, "2026-W47-en", {"linkedin": "urn:li:1"})
    an.save(f, "2026-W48-en", {"facebook": "99"})
    assert an.load(f, "2026-W47-en") == {"linkedin": "urn:li:1"}
    assert set(json.loads(f.read_text(encoding="utf-8"))) == {"2026-W47-en", "2026-W48-en"}


def test_channels_line_names_tiktok_as_drafts():
    from pipeline.publish.social import channels_line
    cfg = {"social": {"platforms": ["youtube", "instagram", "facebook", "tiktok", "linkedin"], "tiktok_mode": "inbox"}}
    assert channels_line(cfg) == "YouTube, Instagram, Facebook and LinkedIn, and to your TikTok drafts"
    cfg["social"]["tiktok_mode"] = "direct"
    assert channels_line(cfg) == "YouTube, Instagram, Facebook, TikTok and LinkedIn"
    assert channels_line({"social": {"platforms": ["youtube"]}}) == "YouTube"


def test_connection_report_does_not_call_a_relayed_platform_unconnected(monkeypatch):
    from pipeline.publish import social
    from scripts import connect
    for k in ("LINKEDIN_TOKEN", "INSTAGRAM_TOKEN", "FACEBOOK_PAGE_TOKEN", "FACEBOOK_PAGE_ID", "BUFFER_API_KEY",
              "YOUTUBE_REFRESH_TOKEN", "TIKTOK_REFRESH_TOKEN", "COMPOSIO_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    bare = connect.check()
    assert "- Instagram: not connected" in bare and "- Facebook: not connected" in bare

    class Fake:
        def __init__(self, *a): pass
        def pages(self): return [{"name": "AI This Week"}]
        def _run(self, *a, **k): return {"username": "aithisweek"}
    monkeypatch.setattr(social, "Composio", Fake)
    monkeypatch.setenv("COMPOSIO_API_KEY", "x")
    text = connect.check()
    assert "- Instagram: not connected" not in text and "- Facebook: not connected" not in text
    assert "- Composio, Instagram: connected as **@aithisweek**" in text and "Page **AI This Week**" in text
