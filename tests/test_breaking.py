import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import yaml

from pipeline import breaking
from pipeline.models import NewsItem

NOW = datetime(2026, 11, 18, 10, tzinfo=timezone.utc)
TEXT = ("Politico counts 6 major outages in 6 days. Microsoft 365 went down on November 12. "
        "Secretary of State Marco Rubio said there is zero evidence of a malign actor. "
        "Downdetector logged 45,000 reports. ") * 6


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
                          hook="Six US outages in six days.", linkedin="Six outages in six days.",
                          question="Would your company trust one cloud provider now?", lines=[
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
    few.lines = few.lines[:2] + few.lines[-2:]
    assert any("lines" in p for p in breaking.mechanical(few, items, LIB))


def test_breaking_and_explainer_shorts_share_one_pace_rule():
    from pipeline import explainer
    assert breaking.SHAPE in breaking.SYSTEM and breaking.SHAPE in explainer.SYSTEM
    assert "6 to 9 lines" in breaking.SHAPE


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
    # Founder 2026-11-24: 1.08 throughout was too fast. Quicker than the episode, never above 1.05.
    assert 1.05 >= vf["tempo_short_en"] > vf["tempo_en"]
    assert "for_short(cfg) if _breaking(out)" in inspect.getsource(run_pipeline)


# --- a Short's pace varies: slower on the opening and the closing line (founder 2026-11-24) -------------------
def test_a_short_slows_for_its_first_and_last_line():
    from pipeline.config import load_settings
    from pipeline.video import voicefirst
    vf = load_settings()["video"]["voicefirst"]
    assert 0.85 <= vf["pace_short_ends"] < 1.0
    short = voicefirst.for_short({"language": "en", "video": {"voicefirst": {"tempo_en": 0.94, "tempo_short_en": 1.04,
                                                                               "pace_short_ends": 0.9}}})
    assert short["video"]["voicefirst"]["pace_ends"] == 0.9
    # pauses heard in a 40 s read: after the first line (3.1 s) and before the last one (35.2 s)
    pauses = [(0.0, 0.1), (3.1, 3.5), (9.0, 9.3), (20.0, 20.4), (35.2, 35.6), (39.9, 40.0)]
    plan = voicefirst.pace_plan(pauses, 40.0, 1.04, 0.9)
    assert [(round(a, 1), round(b, 1), round(x, 3)) for a, b, x in plan] == [(0.0, 3.3, 0.936), (3.3, 35.4, 1.04), (35.4, 40.0, 0.936)]
    # a time in the read lands where the changed pace puts it
    assert abs(voicefirst.warp(3.3, plan) - 3.3 / 0.936) < 1e-6
    assert abs(voicefirst.warp(40.0, plan) - (3.3 / 0.936 + 32.1 / 1.04 + 4.6 / 0.936)) < 1e-6


def test_a_read_with_no_clear_pauses_keeps_one_pace():
    from pipeline.video import voicefirst
    assert voicefirst.pace_plan([], 40.0, 1.04, 0.9) == [(0.0, 40.0, 1.04)]
    assert voicefirst.pace_plan([(3.1, 3.5)], 40.0, 1.04, 1.0) == [(0.0, 40.0, 1.04)]      # no slowing asked for
    assert voicefirst.pace_plan([(3.1, 3.5)], 6.0, 1.04, 0.9) == [(0.0, 6.0, 1.04)]        # too short to shape


# --- an outage needs a measured impact to earn a Short (founder 2026-11-24, the AWS alert-delay story) --------
def test_an_outage_nobody_measured_from_one_outlet_is_not_drafted(tmp_path, monkeypatch):
    aws = json.loads((breaking.ROOT / "reviewed" / "2026-11-24-brk-aws-outage-alert-delay-en" / "items.json").read_text(encoding="utf-8"))
    assert breaking.outage_unmeasured(aws, outlets=1, need=3)                      # one outlet, no count of who was hit
    assert not breaking.outage_unmeasured(aws, outlets=3, need=3)                  # widely carried: it gets its Short
    counted = [{**aws[0], "summary": aws[0]["summary"] + " Downdetector logged more than 45,000 reports."}]
    assert not breaking.outage_unmeasured(counted, outlets=1, need=3)              # an article measures the impact
    for text in ("About 2 million users lost access.", "It grounded 1,400 flights.", "8.1 million reports were filed."):
        assert not breaking.outage_unmeasured([{"title": "Bank app outage", "summary": text}], 1, 3), text
    for text in ("More than 10 major services were affected.", "It lasted 93 minutes on November 15, 2026."):
        assert breaking.outage_unmeasured([{"title": "Cloud outage hits region", "summary": text}], 1, 3), text
    assert not breaking.outage_unmeasured([{"title": "Jensen Huang returns as CEO", "summary": "x"}], 1, 3)   # not an outage

    from pipeline.config import load_settings
    assert load_settings()["breaking"]["outage_min_sources"] >= 3
    assert "outage" in breaking.SYSTEM.lower() and "how many" in breaking.SYSTEM.lower()


def test_run_records_an_unmeasured_outage_as_skipped_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.notify.whatsapp", lambda *a, **k: None)
    monkeypatch.setattr(breaking, "make", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not be drafted")))
    st = {"items": {"a": item(1, "Cloud provider slow to flag regional outage", "Trade Site",
                              text="The outage lasted 93 minutes and hit more than 10 services. " * 20)}}
    done = tmp_path / "breaking.json"
    assert breaking.run({"breaking": {"outage_min_sources": 3}}, st, None, NOW, done, tmp_path) is None
    rec = list(json.loads(done.read_text(encoding="utf-8"))["stories"].values())[0]
    assert rec["skipped"] and "impact" in rec["why"]


def test_a_short_shows_the_real_person_or_head_office_it_names(tmp_path, monkeypatch):
    """Founder 2026-11-27: Shorts show real faces and head offices, as episodes do (licensed Wikimedia photos)."""
    st = state()
    items = breaking._articles(breaking.candidates(st, NOW, set())[0])
    ids = [i.id for i in items]
    d = good_draft(ids)
    d.lines[1].visual = "photo: Microsoft headquarters"
    d.lines[6].visual = "photo: Marco Rubio | Marco Rubio, US Secretary of State"
    assert breaking.mechanical(d, items, LIB) == []
    assert "photo:" in breaking.SYSTEM and "headquarters" in breaking.SYSTEM
    from pipeline import explainer
    assert breaking.VISUALS in breaking.SYSTEM and breaking.VISUALS in explainer.SYSTEM
    script = breaking.script_md(d)
    assert "[Visual: photo Microsoft headquarters]" in script
    assert "[Visual: photo Marco Rubio | Marco Rubio, US Secretary of State]" in script


def test_a_photo_of_someone_the_articles_never_name_is_refused():
    items = breaking._articles(breaking.candidates(state(), NOW, set())[0])
    d = good_draft([i.id for i in items])
    d.lines[6].visual = "photo: Elon Musk | Elon Musk, CEO of Tesla"
    assert any("Elon Musk" in p for p in breaking.mechanical(d, items, LIB))


def test_a_short_asks_one_quick_question_on_screen_and_in_the_folder(tmp_path, monkeypatch):
    """Founder 2026-11-27: invite people to answer. One short question a viewer can answer in a word or two."""
    st = state()
    items = breaking._articles(breaking.candidates(st, NOW, set())[0])
    d = good_draft([i.id for i in items])
    assert breaking.mechanical(d, items, LIB) == []
    for bad, why in [("Would you trust one cloud provider", "?"),
                     ("Should Gulf banks now invest in a second cloud provider for safety?", "money"),
                     ("What do you think about everything that happened with these outages across the whole week?", "words")]:
        d.question = bad
        assert any(why in p for p in breaking.mechanical(d, items, LIB)), bad
    d.question = "Would your company trust one cloud provider now?"
    week = breaking.write(d, items, NOW, {k: "u" for k in LIB}, tmp_path)
    meta = yaml.safe_load((tmp_path / "reviewed" / week / "breaking.yaml").read_text())
    assert meta["question"] == "Would your company trust one cloud provider now?"
    assert "question" in breaking.SYSTEM
