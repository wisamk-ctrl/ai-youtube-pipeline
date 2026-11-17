from pipeline.post import shorts


def test_a_hook_delays_the_story_and_the_end_card():
    g = shorts.filter_graph(40.0, 656, None, "Inter", 30, shorts.HOOK_SECONDS)
    assert "start_duration=2.5" in g and "adelay=2500" in g
    assert "enable='gte(t,42.500)'" in g and "enable='lt(t,2.5)'" in g


def test_without_a_hook_the_short_is_unchanged():
    g = shorts.filter_graph(40.0, 656, None, "Inter", 30)
    assert "start_duration" not in g and "adelay" not in g and "enable='gte(t,40.000)'" in g


def test_hooks_come_from_the_plan_and_the_reviewed_file_wins(tmp_path, monkeypatch):
    out = tmp_path / "output" / "2026-W99-en"
    out.mkdir(parents=True)
    (out / "plan.json").write_text('{"short_hooks": [{"section": "A Story", "hook": "From the plan"}]}', encoding="utf-8")
    assert shorts.hooks_for(out) == {"a story": "From the plan"}
