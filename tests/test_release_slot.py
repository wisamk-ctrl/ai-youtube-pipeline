"""The weekly release slot (founder 2026-11-24): Sunday 07:00 Gulf, so the episode is waiting when the week starts
in Riyadh, Amman and Cairo. Every message that states the time is built from the setting, and a slot that is
missed on the day still goes out that day."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from pipeline.publish import release_status as rs
from pipeline.publish import youtube_upload as yu

ROOT = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))


def test_the_slot_is_sunday_seven_in_the_morning_gulf_time():
    p = CFG["publish"]
    assert p["publish_weekday"] == 6 and p["publish_hour_utc"] == 3       # 03:00 UTC = 07:00 Gulf (UTC+4)
    assert rs.slot_text(CFG) == "Sunday 07:00 Gulf"


def test_a_publish_on_saturday_goes_out_on_sunday_morning(monkeypatch):
    sat = datetime(2026, 11, 28, 18, tzinfo=timezone.utc)
    assert yu.next_publish_time(CFG, now=sat) == datetime(2026, 11, 29, 3, tzinfo=timezone.utc)


def test_a_slot_missed_on_the_day_still_goes_out_that_day_not_a_week_later():
    late = datetime(2026, 11, 29, 5, 30, tzinfo=timezone.utc)          # Sunday 09:30 Gulf, after the slot
    at = yu.next_publish_time(CFG, now=late)
    assert late < at <= late + timedelta(minutes=30)
    monday = datetime(2026, 11, 30, 5, tzinfo=timezone.utc)
    assert yu.next_publish_time(CFG, now=monday) == datetime(2026, 12, 6, 3, tzinfo=timezone.utc)


def test_no_message_states_the_old_time():
    for path in ("pipeline/publish/release_status.py", "scripts/review_issue.py", "scripts/channel.py",
                 "config/monetisation_playbook.md"):
        assert "17:00" not in (ROOT / path).read_text(encoding="utf-8"), path
    assert "Sunday 07:00 Gulf" in rs.publish_reply(CFG, "2026-W48-en", lambda name: True)


def test_the_no_episode_alarm_runs_on_saturday_evening_before_the_slot():
    wf = yaml.safe_load((ROOT / ".github" / "workflows" / "channel.yml").read_text(encoding="utf-8"))
    crons = [c["cron"] for c in wf[True]["schedule"]]
    assert "17 16 * * 6" in crons and "17 4 * * 0" not in crons       # Saturday 20:17 Gulf
    text = (ROOT / ".github" / "workflows" / "channel.yml").read_text(encoding="utf-8")
    assert '"17 16 * * 6") c=watch-publish' in text
