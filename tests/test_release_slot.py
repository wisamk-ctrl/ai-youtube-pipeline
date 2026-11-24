"""The weekly release slot: Sunday 17:00 Gulf (founder 2026-11-17, kept 2026-11-24 after weighing 07:00 and 15:00).
Every message that states the time is built from the setting, and a slot missed on the day still goes out that day."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from pipeline.publish import release_status as rs
from pipeline.publish import youtube_upload as yu

ROOT = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))


def test_the_slot_is_sunday_at_five_in_the_afternoon_gulf_time():
    p = CFG["publish"]
    assert p["publish_weekday"] == 6 and p["publish_hour_utc"] == 13      # 13:00 UTC = 17:00 Gulf (UTC+4)
    assert rs.slot_text(CFG) == "Sunday 17:00 Gulf"
    assert rs.slot_text({"publish": {"publish_weekday": 6, "publish_hour_utc": 22}}) == "Monday 02:00 Gulf"


def test_a_publish_before_the_slot_goes_out_at_the_slot():
    for now in (datetime(2026, 11, 28, 18, tzinfo=timezone.utc), datetime(2026, 11, 29, 9, tzinfo=timezone.utc)):
        assert yu.next_publish_time(CFG, now=now) == datetime(2026, 11, 29, 13, tzinfo=timezone.utc)


def test_a_slot_missed_on_the_day_still_goes_out_that_day_not_a_week_later():
    late = datetime(2026, 11, 29, 15, 30, tzinfo=timezone.utc)         # Sunday 19:30 Gulf, after the slot
    at = yu.next_publish_time(CFG, now=late)
    assert late < at <= late + timedelta(minutes=30)
    monday = datetime(2026, 11, 30, 5, tzinfo=timezone.utc)
    assert yu.next_publish_time(CFG, now=monday) == datetime(2026, 12, 6, 13, tzinfo=timezone.utc)


def test_the_messages_take_the_time_from_the_setting():
    for path in ("pipeline/publish/release_status.py", "scripts/review_issue.py", "scripts/channel.py"):
        assert "17:00" not in (ROOT / path).read_text(encoding="utf-8"), path
    other = {"publish": {**CFG["publish"], "publish_hour_utc": 5}}
    assert "Sunday 17:00 Gulf" in rs.publish_reply(CFG, "2026-W48-en", lambda name: True)
    assert "Sunday 09:00 Gulf" in rs.publish_reply(other, "2026-W48-en", lambda name: True)
