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


def test_with_the_settings_as_they_are_an_episode_goes_public_on_time_without_chapter_pictures(tmp_path, monkeypatch):
    """Founder 2026-11-23: YouTube makes chapter pictures days after publishing, so waiting for them only made
    W47-en late (18:40 Gulf, not 17:00)."""
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    setup(tmp_path, monkeypatch, [{"week": "W", "video_id": "v", "release_at": "2026-11-22T13:00:00Z", "status": "waiting"}])
    made = []
    release.run(datetime(2026, 11, 22, 12, 59, tzinfo=timezone.utc), ready=lambda v: (False, "1 picture for 11 chapters"), make_public=made.append)
    assert made == []
    release.run(datetime(2026, 11, 22, 13, 1, tzinfo=timezone.utc), ready=lambda v: (False, "1 picture for 11 chapters"), make_public=made.append)
    e = release.load()[0]
    assert made == ["v"] and e["status"] == "public" and "on time" in e["note"] and "after 0 h" not in e["note"]
