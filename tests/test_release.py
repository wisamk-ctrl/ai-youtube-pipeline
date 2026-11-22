from datetime import datetime, timezone

from scripts import release


def setup(tmp_path, monkeypatch, entries):
    monkeypatch.setattr(release, "QUEUE", tmp_path / "releases.json")
    release.save(entries)


def test_waits_before_the_release_time_even_when_ready(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, [{"week": "W", "video_id": "v", "release_at": "2026-11-22T13:00:00Z", "status": "waiting"}])
    made = []
    release.run(datetime(2026, 11, 22, 12, tzinfo=timezone.utc), ready=lambda v: (True, "ok"), make_public=made.append, wait_hours=6)
    assert made == [] and release.load()[0]["status"] == "waiting"


def test_publishes_at_the_release_time_once_chapters_are_ready(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, [{"week": "W", "video_id": "v", "release_at": "2026-11-22T13:00:00Z", "status": "waiting"}])
    made = []
    release.run(datetime(2026, 11, 22, 13, 5, tzinfo=timezone.utc), ready=lambda v: (True, "ok"), make_public=made.append, wait_hours=6)
    assert made == ["v"] and release.load()[0]["status"] == "public"


def test_holds_while_chapters_are_not_ready_then_publishes_after_the_wait(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, [{"week": "W", "video_id": "v", "release_at": "2026-11-22T13:00:00Z", "status": "waiting"}])
    made = []
    release.run(datetime(2026, 11, 22, 15, tzinfo=timezone.utc), ready=lambda v: (False, "1 picture"), make_public=made.append, wait_hours=6)
    assert made == []
    release.run(datetime(2026, 11, 22, 19, 1, tzinfo=timezone.utc), ready=lambda v: (False, "1 picture"), make_public=made.append, wait_hours=6)
    assert made == ["v"] and "after 6 h" in release.load()[0]["note"]


def test_a_check_that_cannot_see_the_page_releases_on_time(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, [{"week": "W", "video_id": "v", "release_at": "2026-11-22T13:00:00Z", "status": "waiting"}])
    made = []
    blind = lambda v: (None, "sign-in wall")
    release.run(datetime(2026, 11, 22, 12, tzinfo=timezone.utc), ready=blind, make_public=made.append, wait_hours=6)
    assert made == []
    release.run(datetime(2026, 11, 22, 13, 5, tzinfo=timezone.utc), ready=blind, make_public=made.append, wait_hours=6)
    assert made == ["v"] and "sign-in wall" in release.load()[0]["note"]
