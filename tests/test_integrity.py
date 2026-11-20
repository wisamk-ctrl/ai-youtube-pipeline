"""Channel integrity (scripts/integrity.py). Founder 2026-11-20: "I'm concerned about somebody hijacking the account."
A hijacked YouTube channel is usually renamed and filled with scam uploads within hours; this daily check compares
the channel with yesterday's snapshot and with what the pipeline itself published."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("integrity", Path(__file__).parents[1] / "scripts" / "integrity.py")
integrity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity)

CH = {"snippet": {"title": "AI This Week", "customUrl": "@aithisweek", "description": "Weekly AI news"}}


def vid(i, title="Ep", privacy="public"):
    return {"id": i, "snippet": {"title": title}, "status": {"privacyStatus": privacy}}


def test_snapshot_keeps_what_a_hijacker_changes():
    s = integrity.snapshot(CH, [vid("aaaaaaaaaaa")])
    assert s["title"] == "AI This Week" and s["custom_url"] == "@aithisweek"
    assert s["videos"] == {"aaaaaaaaaaa": "Ep"} and len(s["description_sha"]) == 64


def test_no_change_no_alert():
    s = integrity.snapshot(CH, [vid("aaaaaaaaaaa")])
    assert integrity.diff(s, s, known=set()) == []


def test_an_upload_the_pipeline_did_not_make_is_an_alert_but_ours_is_not():
    base = integrity.snapshot(CH, [vid("aaaaaaaaaaa")])
    now = integrity.snapshot(CH, [vid("aaaaaaaaaaa"), vid("bbbbbbbbbbb", "Ours"), vid("ccccccccccc", "FREE CRYPTO LIVE")])
    alerts = integrity.diff(base, now, known={"bbbbbbbbbbb"})
    assert len(alerts) == 1 and "FREE CRYPTO LIVE" in alerts[0] and "ccccccccccc" in alerts[0]


def test_rename_handle_description_and_lost_videos_are_alerts():
    base = integrity.snapshot(CH, [vid("aaaaaaaaaaa", "W46")])
    hijacked = {"snippet": {"title": "Tesla Live", "customUrl": "@teslalive2026", "description": "x"}}
    alerts = integrity.diff(base, integrity.snapshot(hijacked, []), known=set())
    text = "\n".join(alerts)
    assert "Tesla Live" in text and "@teslalive2026" in text and "description" in text and "W46" in text


def test_known_ids_come_from_our_publishing_records(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "social_queue.json").write_text(
        '[{"posts": {"youtube": {"url": "https://youtube.com/shorts/qTjAbc12345"}}}, {"x": "https://youtu.be/ihIQxeRtcu4"}]')
    (tmp_path / "reviewed" / "W").mkdir(parents=True)
    (tmp_path / "reviewed" / "W" / "meta.yaml").write_text("youtube_video_id: Zz9_-Yy8XwV\n")
    assert integrity.known_ids(tmp_path) >= {"qTjAbc12345", "ihIQxeRtcu4", "Zz9_-Yy8XwV"}
