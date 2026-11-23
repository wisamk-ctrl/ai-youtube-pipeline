"""Where a release goes, said truthfully (2026-11-23): the `publish` reply named only LinkedIn and Facebook, a
platform with no secrets was skipped with an info-level log line, WhatsApp alerts were silently off, and the
messages named every configured platform whether it was connected or not. One function reads the settings and
which secrets are present; every message is built from it."""
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from pipeline.publish import release_status as rs
from pipeline.publish import social

ROOT = Path(__file__).resolve().parent.parent
CFG = {"publish": {"privacy": "private"},
       "social": {"platforms": ["youtube", "instagram", "facebook", "tiktok", "linkedin"], "tiktok_mode": "inbox",
                  "whatsapp_channel_url": "https://whatsapp.com/channel/x"}}
TODAY = {"GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN", "LINKEDIN_TOKEN", "TIKTOK_CLIENT_KEY",
         "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN", "COMPOSIO_API_KEY"}          # the repo's secrets on 2026-11-23
today = lambda name: name in TODAY
nothing = lambda name: False
everything = lambda name: True


def test_status_follows_the_secrets_that_are_present():
    assert rs.shorts(CFG, today) == {"youtube": "auto", "instagram": "relay", "facebook": "relay", "tiktok": "drafts",
                                     "linkedin": "auto"}
    assert rs.episode(CFG, today) == {"youtube": "auto", "linkedin": "auto", "facebook": "link", "instagram": "none",
                                      "tiktok": "none"}
    assert set(rs.shorts(CFG, nothing).values()) == {"off"}
    assert rs.episode(CFG, everything)["facebook"] == "auto" and rs.shorts(CFG, everything)["instagram"] == "auto"
    direct = {"social": {**CFG["social"], "tiktok_mode": "direct"}}
    assert rs.shorts(direct, today)["tiktok"] == "auto"


def test_posters_and_the_status_read_one_table_of_secrets():
    assert social.NEEDS is rs.NEEDS and set(rs.NEEDS) == set(social.PLATFORMS)


def test_publish_reply_names_every_platform_and_what_is_off():
    msg = rs.publish_reply(CFG, "2026-W48-en", today)
    assert "`2026-W48-en`" in msg and "private" in msg and "unlisted" not in msg
    for needle in ("LinkedIn", "Facebook", "link post", "Instagram", "TikTok", "drafts", "WhatsApp Channel",
                   "by hand", "alerts to your phone are off"):
        assert needle in msg, needle
    assert "alerts to your phone are off" not in rs.publish_reply(CFG, "2026-W48-en", everything)
    # Founder 2026-11-23: the weekly episode's own Shorts stay off; only breaking Shorts are posted.
    assert "Breaking Shorts" in msg and "weekly episode's own Shorts are not posted" in msg and "plan and approve" not in msg
    off = rs.publish_reply(CFG, "2026-W48-en", nothing)
    assert "not connected" in off and "LinkedIn" in off


def test_the_reply_script_runs_with_flags_instead_of_secret_values():
    env = {"PATH": "/usr/bin:/bin", **{k: "1" for k in TODAY}}
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "release_plan.py"), "2026-W48-en"], env=env,
                         capture_output=True, text=True, check=True).stdout
    assert "Publishing `2026-W48-en`" in out and "link post" in out


def test_approve_workflow_builds_its_reply_from_the_code_and_passes_no_secret_value():
    text = (ROOT / ".github" / "workflows" / "approve.yml").read_text(encoding="utf-8")
    job = yaml.safe_load(text)["jobs"]["act"]
    assert "scripts/release_plan.py" in text and "LinkedIn and Facebook follow" not in text
    for name in sorted({k for need in rs.NEEDS.values() for k in need} | set(rs.RELAY) | set(rs.ALERTS)):
        assert job["env"][name] == "${{ secrets.%s != '' && '1' || '' }}" % name, name
    assert text.rindex("gh workflow run weekly.yml") < text.index("python3 scripts/release_plan.py")   # publishing never waits on the message


def test_channels_line_names_only_what_is_connected():
    assert social.channels_line(CFG, today) == "YouTube, Instagram, Facebook and LinkedIn, and to your TikTok drafts"
    only = lambda name: name in rs.NEEDS["youtube"]
    assert social.channels_line(CFG, only) == "YouTube (not connected, so skipped: Instagram, Facebook, TikTok and LinkedIn)"
    assert social.channels_line(CFG, nothing).startswith("nowhere yet")


def test_a_platform_with_no_secrets_is_reported_not_passed_over(caplog):
    e = {"id": "2026-W48-en#1", "week": "2026-W48-en", "file": "s.mp4", "approved": True, "due": "2026-11-20T00:00:00Z",
         "captions": {}, "posts": {"youtube": {"status": "queued"}, "instagram": {"status": "queued"}}}
    lines = social.post_due([e], CFG, lambda _e: Path("s.mp4"), {"youtube": lambda _e, _p: {"url": "u"}},
                            now=datetime(2026, 11, 23, tzinfo=timezone.utc))
    assert any(x.startswith("⏭️") and "instagram" in x and "not connected" in x for x in lines)
    assert e["posts"]["instagram"]["status"] == "queued" and "not connected" in e["posts"]["instagram"]["note"]
    assert not any(x.startswith(("❌", "⚠️")) for x in lines)                 # reported, and the run still passes
    with caplog.at_level(logging.WARNING):
        for k in rs.NEEDS["linkedin"] + rs.RELAY:
            import os
            os.environ.pop(k, None)
        social.posters({"social": {"platforms": ["linkedin"]}})
    assert "linkedin not connected" in caplog.text


def test_alerts_that_are_off_say_so_once(monkeypatch, caplog):
    from scripts import health, notify
    monkeypatch.delenv("WHATSAPP_PHONE", raising=False)
    monkeypatch.delenv("CALLMEBOT_APIKEY", raising=False)
    monkeypatch.setattr(notify, "_warned", False)
    with caplog.at_level(logging.WARNING):
        assert notify.whatsapp("one") is False and notify.whatsapp("two") is False
    assert caplog.text.count("WhatsApp alerts are off") == 1
    assert "WhatsApp alerts are off" in health.alert_note(nothing) and health.alert_note(everything) == ""


def test_breaking_short_on_linkedin_keeps_the_whatsapp_link(tmp_path):
    import json
    from scripts import breaking_post
    week = "2026-11-23-brk-test-en"
    (tmp_path / "reviewed" / week).mkdir(parents=True)
    (tmp_path / "reviewed" / week / "breaking.yaml").write_text("linkedin: Six outages in six days.\n", encoding="utf-8")
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.yaml").write_text(yaml.safe_dump({"social": CFG["social"]}), encoding="utf-8")
    q = tmp_path / "q.json"
    q.write_text(json.dumps([{"week": week, "captions": {"linkedin": "old", "tiktok": ""}}]), encoding="utf-8")
    assert breaking_post.approve(week, queue=q, root=tmp_path) == 1
    cap = json.loads(q.read_text(encoding="utf-8"))[0]["captions"]["linkedin"]
    assert cap.startswith("Six outages") and "Follow on WhatsApp: https://whatsapp.com/channel/x" in cap


def test_settings_comment_no_longer_promises_the_link_on_every_caption():
    text = (ROOT / "config" / "settings.yaml").read_text(encoding="utf-8")
    line = next(x for x in text.splitlines() if x.strip().startswith("whatsapp_channel_url:"))
    assert "every Short's caption" not in line and "YouTube, LinkedIn and Facebook" in line


def test_no_weekly_short_is_left_waiting_in_the_queue():
    """Founder 2026-11-23: weekly Shorts stay off, so an unapproved weekly entry must not sit there as 'waiting'."""
    import json
    import re
    q = json.loads((ROOT / "data" / "social_queue.json").read_text(encoding="utf-8"))
    waiting = [e["id"] for e in q if re.match(r"\d{4}-W\d{2}", e["week"]) and not e.get("approved")
               and any(r.get("status") == "queued" for r in e["posts"].values())]
    assert waiting == []
