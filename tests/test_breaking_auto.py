"""Founder 2026-11-25: breaking Shorts post on their own, without `post <week>`, until the test window ends,
unless the pipeline is not sure (the automatic check flagged something)."""
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts.breaking_auto import decide

ROOT = Path(__file__).resolve().parents[1]
OK = "✅ **Automatic check passed** (62 s, -14.0 LUFS)"
BAD = "⚠️ **Automatic check: 1 to look at** (62 s)\n- dead air 1.5 s at 30.0 s"
CFG = {"breaking": {"auto_post_until": "2026-11-29T23:59:00+04:00"}}
WED = datetime(2026, 11, 25, 12, 0, tzinfo=timezone.utc)


def test_posts_a_clean_breaking_short_inside_the_window():
    post, why = decide("2026-11-25-brk-x-en", OK, CFG, WED)
    assert post, why


def test_holds_when_the_check_flags_anything():
    post, why = decide("2026-11-25-brk-x-en", BAD, CFG, WED)
    assert not post and "dead air" in why


def test_holds_when_there_is_no_check_at_all():
    assert not decide("2026-11-25-brk-x-en", "", CFG, WED)[0]


def test_window_ends_and_founder_ok_is_needed_again():
    after = datetime(2026, 11, 29, 20, 0, tzinfo=timezone.utc)    # Mon 00:00 Dubai
    assert not decide("2026-11-30-brk-x-en", OK, CFG, after)[0]
    assert not decide("2026-11-25-brk-x-en", OK, {"breaking": {}}, WED)[0]


def test_explainer_shorts_still_wait_for_the_founder():
    assert not decide("2026-11-25-exp-x-en", OK, CFG, WED)[0]


def test_settings_carry_the_window_to_sunday_dubai():
    s = yaml.safe_load((ROOT / "config" / "settings.yaml").read_text(encoding="utf-8"))
    assert str(s["breaking"]["auto_post_until"]).startswith("2026-11-29T23:59")


def test_render_dispatches_the_post_and_post_workflow_accepts_it():
    weekly = (ROOT / ".github/workflows/weekly.yml").read_text(encoding="utf-8")
    assert "scripts/breaking_auto.py" in weekly and "gh workflow run breaking-post.yml" in weekly
    post = yaml.safe_load((ROOT / ".github/workflows/breaking-post.yml").read_text(encoding="utf-8"))
    on = post.get("on") or post.get(True)
    assert "week" in on["workflow_dispatch"]["inputs"]
    assert "workflow_dispatch" in post["jobs"]["post"]["if"]
