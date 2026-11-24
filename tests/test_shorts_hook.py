from pipeline.post import shorts


def test_a_hook_delays_the_story_and_the_end_card():
    g = shorts.filter_graph(40.0, 656, None, "Inter", 30, shorts.HOOK_SECONDS)
    assert "start_duration=2.5" in g and "adelay=2500" in g
    assert "enable='gte(t,42.500)'" in g and "enable='lt(t,2.5)'" in g


def test_an_overlay_hook_starts_the_voice_at_once():
    g = shorts.filter_graph(30.0, 656, None, "Inter", 30, 0.0, overlay=2.0)
    assert "start_duration" not in g and "adelay" not in g and "[4:a]" not in g
    assert "[3:v]overlay=0:0:shortest=1:enable='lt(t,2.0)'" in g and "enable='gte(t,30.000)'" in g
    page = shorts.hook_overlay_html("OpenAI just changed the rules", 656)
    assert "background:transparent" in page and "OpenAI just changed the rules" in page


def test_without_a_hook_the_short_is_unchanged():
    g = shorts.filter_graph(40.0, 656, None, "Inter", 30)
    assert "start_duration" not in g and "adelay" not in g and "enable='gte(t,40.000)'" in g


def test_music_carries_the_pauses_and_the_voice_is_levelled_alone():
    g = shorts.filter_graph(40.0, 656, None, "Inter", 30, shorts.HOOK_SECONDS, (5, -12.0))
    assert "[5:a]atrim" in g and "amix=inputs=3" in g
    assert g.index("loudnorm") < g.index("amix")
    fixed = shorts.filter_graph(40.0, 656, None, "Inter", 30, 0.0, (3, -12.0), 3.5)
    assert "volume=3.50dB" in fixed and "loudnorm" not in fixed


def test_hooks_come_from_the_plan_and_the_reviewed_file_wins(tmp_path, monkeypatch):
    out = tmp_path / "output" / "2026-W99-en"
    out.mkdir(parents=True)
    (out / "plan.json").write_text('{"short_hooks": [{"section": "A Story", "hook": "From the plan"}]}', encoding="utf-8")
    assert shorts.hooks_for(out) == {"a story": "From the plan"}
