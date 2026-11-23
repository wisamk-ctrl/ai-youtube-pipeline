import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import yaml

from pipeline import breaking
from pipeline.models import NewsItem

NOW = datetime(2026, 11, 18, 10, tzinfo=timezone.utc)
TEXT = ("Politico counts 6 major outages in 6 days. Microsoft 365 went down on November 12. "
        "Secretary of State Marco Rubio said there is zero evidence of a malign actor. ") * 6


def item(n, title, source, text=TEXT, flagged=True, seen="2026-11-18T08:00"):
    i = NewsItem(source=source, source_type="rss", title=title, summary=text, url=f"https://x/{n}",
                 published=datetime(2026, 11, 18, 7, tzinfo=timezone.utc))
    return {**i.to_dict(), "first_seen": seen, "flagged": flagged}


def state():
    return {"items": {d["id"]: d for d in [
        item(1, "Six US outages in six days, what we know", "Politico"),
        item(2, "Six US outages in six days: what we know so far", "Gulf News"),
        item(3, "A small product update", "Blog", flagged=False),
        item(4, "Old flagged story", "AP", seen="2026-11-17T01:00"),
        item(5, "Thin flagged story", "X", text="short"),
    ]}}


def good_draft(ids, number_line="Politico counts 6 major outages in 6 days."):
    L = breaking.Line
    return breaking.Draft(newsworthy=True, slug="six outages", title="Six US Outages in Six Days",
                          hook="Six US outages in six days.", linkedin="Six outages in six days.", lines=[
        L(text=number_line, visual="number: 6 | Major US outages in 6 days", sources=[ids[0]]),
        L(text="Microsoft 365 went down on November 12.",
          visual="clip: office tower at night, floors going dark", sources=[ids[0]]),
        L(text="More systems followed in the days after it.",
          visual="clip: server hall with one dark row of racks", sources=[ids[0]]),
        L(text="Banks, airlines and a security agency all reported problems.",
          visual="clip: network traffic jamming at a gateway ring", sources=[ids[1]]),
        L(text="It all happened during the same busy week.",
          visual="clip: three data centers linked by bridges of light", sources=[ids[1]]),
        L(text="So was it an attack, as many people online have been asking?",
          visual="title: Was it an attack?", sources=[ids[1]]),
        L(text="Secretary of State Marco Rubio said there is zero evidence of a malign actor.",
          visual="clip: network traffic jamming at a gateway ring", sources=[ids[0]]),
        L(text="No single cause has been named for the failures so far.",
          visual="clip: server hall with one dark row of racks", sources=[ids[0]]),
        L(text="For businesses in the Gulf, the thing to watch is how much depends on a single provider.",
          visual="clip: three data centers linked by bridges of light", sources=[]),
    ])


LIB = ["office tower at night, floors going dark", "server hall with one dark row of racks",
       "network traffic jamming at a gateway ring", "three data centers linked by bridges of light"]


def test_candidates_groups_recent_flagged_stories_with_text():
    c = breaking.candidates(state(), NOW, set())
    assert len(c) == 1 and len(c[0]) == 2 and {d["source"] for d in c[0]} == {"Politico", "Gulf News"}
    assert breaking.candidates(state(), NOW, {breaking._norm(c[0][0]["title"])[:80]}) == []


def test_mechanical_passes_a_good_draft_and_catches_a_figure_not_in_the_sources():
    items = breaking._articles(breaking.candidates(state(), NOW, set())[0])
    ids = [i.id for i in items]
    assert breaking.mechanical(good_draft(ids), items, LIB) == []
    bad = good_draft(ids, "Politico counts 9 major outages in 9 days.")
    assert any("figures" in p for p in breaking.mechanical(bad, items, LIB))


class FakeClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.messages = SimpleNamespace(parse=self.parse)

    def parse(self, **kw):
        return SimpleNamespace(parsed_output=self.outputs.pop(0), stop_reason="end_turn", usage=None)


def test_run_writes_a_folder_the_render_can_use(tmp_path, monkeypatch):
    st = state()
    items = breaking._articles(breaking.candidates(st, NOW, set())[0])
    client = FakeClient([good_draft([i.id for i in items]), breaking.Verdict(unsupported=[])])
    monkeypatch.setattr(breaking, "LIBRARY", tmp_path / "lib.yaml")
    (tmp_path / "lib.yaml").write_text(yaml.safe_dump({"clips": {k: f"https://v/{n}.mp4" for n, k in enumerate(LIB)}}))
    week = breaking.run({"scripting": {}}, st, client, NOW, tmp_path / "done.json", tmp_path)
    assert week == "2026-11-18-brk-six-outages-en"
    f = tmp_path / "reviewed" / week
    script = (f / "script.md").read_text()
    assert script.startswith("[Section: Six US Outages in Six Days]") and "[Visual: number 6 | Major US outages in 6 days]" in script
    assert "[Visual: stock office tower at night, floors going dark]" in script
    assert yaml.safe_load((f / "breaking.yaml").read_text())["outro"].endswith("shorts_outro_breaking_en.wav")
    assert len(json.loads((f / "items.json").read_text())) == 2
    assert set(yaml.safe_load((f / "visuals.yaml").read_text())) <= set(LIB)
    # the same story is not drafted twice
    assert breaking.run({"scripting": {}}, st, FakeClient([]), NOW, tmp_path / "done.json", tmp_path) is None


def test_a_draft_that_fails_the_second_check_twice_is_dropped(tmp_path, monkeypatch):
    st = state()
    items = breaking._articles(breaking.candidates(st, NOW, set())[0])
    d = good_draft([i.id for i in items])
    client = FakeClient([d, breaking.Verdict(unsupported=[3]), d, breaking.Verdict(unsupported=[3])])
    monkeypatch.setattr(breaking, "LIBRARY", tmp_path / "lib.yaml")
    (tmp_path / "lib.yaml").write_text(yaml.safe_dump({"clips": {k: "https://v.mp4" for k in LIB}}))
    assert breaking.run({"scripting": {}}, st, client, NOW, tmp_path / "done.json", tmp_path) is None
    assert any(v.get("skipped") for v in json.loads((tmp_path / "done.json").read_text())["stories"].values())


def test_the_daily_limit_counts_distinct_shorts_not_headlines(tmp_path, monkeypatch):
    done = {"stories": {f"h{n}": {"at": "2026-11-18T07:40", "week": "2026-11-18-brk-a-en", "by_hand": True} for n in range(28)}}
    (tmp_path / "done.json").write_text(json.dumps(done))
    st = state()
    items = breaking._articles(breaking.candidates(st, NOW, set())[0])
    client = FakeClient([good_draft([i.id for i in items]), breaking.Verdict(unsupported=[])])
    monkeypatch.setattr(breaking, "LIBRARY", tmp_path / "lib.yaml")
    (tmp_path / "lib.yaml").write_text(yaml.safe_dump({"clips": {k: "https://v.mp4" for k in LIB}}))
    assert breaking.run({"scripting": {}}, st, client, NOW, tmp_path / "done.json", tmp_path)


# ── Repeats (founder 2026-11-20: five more outage drafts after the outage Short had been posted) ──
POSTED_18_NOV = ["Microsoft reveals hidden bug behind global Outlook and Microsoft 365 outage",
                 "A string of tech outages disrupted flights, banking, and major apps. Here's what officials have said",
                 "6 major outages in 6 days: From Outlook to the NSA, what we know so far"]


def test_a_new_headline_on_a_story_drafted_in_the_last_days_is_a_repeat():
    assert breaking.is_repeat(["Why so many critical tech outages are happening all at once"], POSTED_18_NOV)
    assert breaking.is_repeat(["Microsoft hit with Canadian class actions over massive outage"], POSTED_18_NOV)
    assert not breaking.is_repeat(["Why Anthropic Stock Is Up (and Down) Today"], POSTED_18_NOV)
    assert not breaking.is_repeat(["Microsoft launches a new Copilot model for Excel"], POSTED_18_NOV)   # one shared word


def test_recent_titles_cover_drafted_stories_inside_the_window():
    old_at = (NOW - timedelta(days=2)).isoformat(timespec="minutes")
    stories = {breaking._norm(t)[:80]: {"at": old_at, "title": t, "week": "2026-11-18-brk-outages-en"} for t in POSTED_18_NOV}
    recent = breaking.recent_titles({"stories": stories}, NOW, days=4)
    assert set(recent) == set(POSTED_18_NOV)
    assert breaking.recent_titles({"stories": stories}, NOW + timedelta(days=1), days=4) != []    # 3 days old
    assert breaking.recent_titles({"stories": stories}, NOW + timedelta(days=3), days=4) == []    # 5 days old
    skipped = {k: dict(v, skipped=True, week=None) for k, v in stories.items()}
    assert breaking.recent_titles({"stories": skipped}, NOW, days=4) == []     # a failed draft does not block a retry


# --- pace (founder 2026-11-23: viewers find the Shorts slow) ---------------------------------------------------
def test_a_short_is_many_short_lines_with_a_quick_first_one():
    items = breaking._articles(breaking.candidates(state(), NOW, set())[0])
    ids = [i.id for i in items]
    slow_start = good_draft(ids, "Politico, the American news site, now counts 6 major outages in only 6 days of this month.")
    assert any("first line" in p for p in breaking.mechanical(slow_start, items, LIB))
    long_line = good_draft(ids)
    long_line.lines[2].text = "More systems followed in the days after it, " * 3
    assert any("line 3" in p and "words" in p for p in breaking.mechanical(long_line, items, LIB))
    few = good_draft(ids)
    few.lines = few.lines[:3] + few.lines[-3:]
    assert any("lines" in p for p in breaking.mechanical(few, items, LIB))


def test_breaking_and_explainer_shorts_share_one_pace_rule():
    from pipeline import explainer
    assert breaking.SHAPE in breaking.SYSTEM and breaking.SHAPE in explainer.SYSTEM
    assert "9 to 12 lines" in breaking.SHAPE


def test_a_short_is_spoken_faster_than_the_episode():
    import inspect
    import run_pipeline
    from pipeline.config import load_settings
    from pipeline.video import voicefirst
    cfg = {"language": "en", "video": {"voicefirst": {"tempo_en": 0.94, "tempo_short_en": 1.08}}}
    fast = voicefirst.for_short(cfg)
    assert fast["video"]["voicefirst"]["tempo_en"] == 1.08 and cfg["video"]["voicefirst"]["tempo_en"] == 0.94
    assert voicefirst.for_short({"language": "ar", "video": {"voicefirst": {"tempo": 1.0}}})["video"]["voicefirst"]["tempo"] == 1.0
    vf = load_settings()["video"]["voicefirst"]
    assert vf["tempo_short_en"] > 1.0 > vf["tempo_en"]
    assert "for_short(cfg) if _breaking(out)" in inspect.getsource(run_pipeline)
