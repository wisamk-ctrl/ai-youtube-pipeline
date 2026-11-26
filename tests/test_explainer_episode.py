"""Evergreen explainer episodes (pipeline/explainer_episode.py, founder 2026-11-26)."""
import json
from types import SimpleNamespace

from pipeline import explainer_episode as xe


def test_items_load_from_research_with_their_research_id(tmp_path):
    (tmp_path / "items.json").write_text(json.dumps([
        {"id": "01-x-01", "title": "Falcon", "source": "TII", "url": "https://tii.ae/f", "published": "2025-05-21",
         "summary": "Falcon Arabic was released.", "source_type": "primary"},
        {"id": "01-x-02", "title": "No url", "source": "?", "url": "", "summary": "dropped"}]))
    items = xe.load_items(tmp_path)
    assert len(items) == 1 and items[0].summary.startswith("[research id 01-x-01]")
    assert str(items[0].published.date()) == "2025-05-21"


def test_problems_list_length_opening_and_critic_fixes():
    long_hook = "[Section: Opening]\n" + "word " * 60 + "\n[Section: One]\nHi everyone, welcome to AI This Week.\n"
    crit = {"worst_three": [{"where": "opening", "problem": "too slow", "fix": "cut"}],
            "defects": [{"severity": "major", "axis": "hook", "rule": "greeting first", "quote": "Hi everyone"}]}
    out = xe.problems_for(long_hook, 1500, crit)
    assert out[0].startswith("Length") and any("hook-words" in p for p in out)
    assert any("too slow" in p for p in out) and any("greeting first" in p for p in out)


def test_write_episode_revises_once_and_writes_the_review_files(tmp_path, monkeypatch):
    (tmp_path / "items.json").write_text(json.dumps([{"id": "a", "title": "T", "source": "S", "url": "https://s/1",
                                                      "published": "2025-01-01", "summary": "Fact."}]))
    (tmp_path / "research.md").write_text("Facts and outline.")
    draft = "[Section: Opening]\nShort hook.\n" + "Fact. " * 40
    calls = []

    class C:
        class messages:
            @staticmethod
            def create(**kw):
                calls.append(kw)
                return SimpleNamespace(content=[SimpleNamespace(type="text", text=draft)])
    from pipeline.scripting import source_map, translate
    monkeypatch.setattr(translate, "critique_en", lambda s, cfg, client: {"minimum": 7, "worst_three": [], "defects": []})
    monkeypatch.setattr(source_map, "build", lambda s, items, model, client, lang="en": ([], None))
    monkeypatch.setattr(source_map, "stats", lambda m: {"unsourced": 0, "claims": 3})
    monkeypatch.setattr(source_map, "render_md", lambda s, m, i: "# map")
    s = xe.write_episode(tmp_path, {"scripting": {"model": "m"}}, "AI in the Gulf", "Next one", 500, C())
    assert len(calls) == 2 and "Next one" in calls[0]["messages"][0]["content"]
    assert (tmp_path / "script.md").exists() and (tmp_path / "checks.md").exists() and s["critic_min"] == 7
