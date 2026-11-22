"""Story ranking for the episode and the Shorts (docs/plans/2026-11-22-news-ranking.md, founder 2026-11-22).
Stories are ranked, never articles; the model gives 0-3 per criterion with a reason and the code does the sums,
the gates and the slots; the founder approves or overrides the list before the script is written."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from pipeline.models import NewsItem
from pipeline.ranking import cluster as cl
from pipeline.ranking import judge as jd
from pipeline.ranking import rank

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
NOW = datetime(2026, 11, 22, 12, tzinfo=timezone.utc)
CFG = {"scoring": {"min_score": 0.5, "max_items": 30, "dedupe_similarity": 0.82,
                   "min_per_region": {"africa": 1, "turkey": 1}, "flagged_seats": 3},
       "ranking": {}}


def item(title, source, hours=10, region="", score=5.0, summary="enterprise adoption of AI agents", url=None):
    return NewsItem(source=source, source_type="rss", title=title, summary=summary,
                    url=url or f"https://{source.lower().replace(' ', '')}.example/{abs(hash(title))}",
                    published=NOW - timedelta(hours=hours), region=region, score=score)


def st(sid, kind="global", d=2, r=2, e=2, t=1, **kw):
    """A clustered story plus the judgement the model (or the fallback) would return for it."""
    story = {"id": sid, "title": kw.pop("title", f"Story {sid}"), "items": kw.pop("items", []),
             "outlets": ["Reuters"], "outlet_count": 1, "tiers": ["A"], "verified": kw.pop("verified", True),
             "repeat": kw.pop("repeat", []), "regions": kw.pop("regions", []), "flagged": False,
             "published": (NOW - timedelta(hours=kw.pop("hours", 20))).isoformat(), "text": kw.pop("text", "G42 Abu Dhabi")}
    j = {"kind": kind, "regional_actor": kw.pop("actor", "G42"), "new_development": kw.pop("new", False),
         "depth": kw.pop("depth", True), "kill": kw.pop("kill", "none"), "decision_frame": "cost",
         "short": kw.pop("short", None),
         **{c: {"score": v, "reason": f"{c} because"} for c, v in
            zip(("decision_impact", "regional_consequence", "evidence", "tension"), (d, r, e, t))}}
    assert not kw, kw
    return story, j


def ranked(pairs, cfg=CFG, overrides=None):
    r = {"week": "2026-W48", "stories": [s for s, _ in pairs], "overrides": overrides or [], "thesis": "",
         "judge": "test", "approved": None}
    rank.score(r["stories"], {s["id"]: j for s, j in pairs}, cfg)
    rank.assign_slots(r, cfg, now=NOW)
    return r


def slot(r, name):
    return [s["id"] for s in sorted(r["stories"], key=lambda s: s.get("position", 99)) if s["slot"] == name]


# ── 1. clustering ────────────────────────────────────────────────────────────
def test_many_outlets_on_one_story_make_one_story_and_outlet_count_is_only_a_signal():
    ipo = [item(f"Anthropic files for IPO at record valuation {k}", f"Outlet{k}") for k in range(6)]
    solo = [item("Saudi Humain signs sovereign cloud deal with Aramco", "Arab News")]
    stories = cl.cluster(ipo + solo, CFG)
    assert len(stories) == 2
    big = next(s for s in stories if "Anthropic" in s["title"])
    assert big["outlet_count"] == 6 and len(big["items"]) <= rank.opts(CFG)["items_per_story"]
    # Same judgement, six outlets against one: the same total. Coverage never multiplies the score.
    j = st("x")[1]
    rank.score(stories, {s["id"]: dict(j) for s in stories}, CFG)
    assert len({s["total"] for s in stories}) == 1


def test_cluster_keeps_at_most_max_stories_and_ids_are_stable():
    words = "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima".split()
    items = [item(f"{w} {w}corp unveils {w}model", f"Src{n}", score=10 - n * 0.1) for n, w in enumerate(words)]
    cfg = {**CFG, "ranking": {"max_stories": 5}}
    a, b = cl.cluster(items, cfg), cl.cluster(list(reversed(items)), cfg)
    assert len(a) == 5 and [s["id"] for s in a] == [s["id"] for s in b]
    assert len({s["id"] for s in a}) == 5


def test_cluster_marks_verified_by_tier_and_repeats_from_earlier_episodes():
    stories = cl.cluster([item("Nvidia export rules tighten for Gulf chip buyers", "Reuters"),
                          item("Tiny startup claims quantum agent breakthrough", "Some Blog")], CFG,
                         covered=["Nvidia export rules for Gulf chip buyers explained"])
    by = {("Nvidia" in s["title"]): s for s in stories}
    assert by[True]["verified"] and by[True]["repeat"]
    assert not by[False]["verified"] and not by[False]["repeat"]


def test_generic_words_do_not_merge_stories_and_one_stray_article_gives_no_region_seat():
    a = item("SDAIA launches artificial intelligence initiative across Saudi universities", "SPA", region="gulf")
    b = item("Nvidia artificial intelligence chips reach Chinese buyers despite curbs", "Reuters", region="cn")
    assert len(cl.cluster([a, b], CFG)) == 2
    same = [item(f"Humain signs Aramco sovereign cloud contract {k}", f"Out{k}", region="gulf") for k in range(5)]
    stray = item("Humain signs Aramco sovereign cloud contract, Ankara watches", "Out9", region="turkey", score=1.0)
    (story,) = cl.cluster(same + [stray], CFG)
    assert "gulf" in story["regions"] and "turkey" not in story["regions"]


# ── 3. scoring: the model scores, the code does the arithmetic ───────────────
def test_code_applies_the_weights_and_ignores_any_total_from_the_model():
    s, j = st("a", d=3, r=2, e=1, t=0)
    j["total"] = 99
    rank.score([s], {"a": j}, CFG)
    assert s["total"] == 3 * 3 + 2 * 2 + 1 * 1 + 0 and s["max_total"] == 21
    s2, j2 = st("b", d=7, r=-2, e=1, t=1)                      # out-of-range scores are clamped to 0..3
    rank.score([s2], {"b": j2}, CFG)
    assert s2["scores"]["decision_impact"]["score"] == 3 and s2["scores"]["regional_consequence"]["score"] == 0


def test_regional_consequence_needs_a_named_actor_found_in_the_sources():
    s, j = st("a", r=3, actor="Ministry of Imaginary Affairs", text="OpenAI ships a model. Analysts say the Gulf may care.")
    rank.score([s], {"a": j}, CFG)
    assert s["scores"]["regional_consequence"]["score"] == 1
    assert "named" in s["scores"]["regional_consequence"]["reason"]
    s, j = st("b", r=3, actor="Humain", text="Saudi's HUMAIN signed with Aramco")
    rank.score([s], {"b": j}, CFG)
    assert s["scores"]["regional_consequence"]["score"] == 3


# ── 2. gates ─────────────────────────────────────────────────────────────────
def test_gates_keep_stories_out_of_the_episode_but_some_can_be_radar():
    r = ranked([st("ok", d=3), st("unver", d=3, verified=False), st("thin", d=3, depth=False),
                st("kill", d=3, kill="funding_no_consequence"), st("old", d=3, repeat=["covered headline"]),
                st("oldnew", d=3, repeat=["covered headline"], new=True),
                st("glob0", kind="global", d=3, r=0, actor="")])
    by = {s["id"]: s for s in r["stories"]}
    assert set(slot(r, "deep")) == {"ok", "oldnew"}
    assert not slot(r, "quick")
    assert set(slot(r, "radar")) <= {"unver", "thin", "kill", "glob0"} and len(slot(r, "radar")) == 3
    assert by["old"]["slot"] == "out" and "covered headline" in by["old"]["gates"]["new"]["reason"]
    assert by["glob0"]["gates"]["kill"]["pass"] is False and "regional" in by["glob0"]["gates"]["kill"]["reason"]
    # The keyword fallback cannot judge a consequence, so it never puts a story on the kill list for lacking one.
    s, j = st("fb", kind="global", r=0, actor="")
    rank.score([s], {"fb": {**j, "judged_by": jd.FALLBACK}}, CFG)
    assert s["gates"]["kill"]["pass"] is True
    assert by["unver"]["gates"]["verified"]["pass"] is False


# ── 4. slots ─────────────────────────────────────────────────────────────────
def test_three_deep_with_a_global_and_a_regional_then_three_quick_three_radar():
    pairs = [st(f"g{n}", "global", d=3, r=2, e=2, t=3 - n) for n in range(4)] + \
            [st("reg", "regional", d=2, r=3, e=1, t=0)] + [st(f"q{n}", "global", d=2, r=1, e=1, t=n % 2) for n in range(6)]
    r = ranked(pairs)
    deep = slot(r, "deep")
    assert len(deep) == 3 and "reg" in deep and deep[0] == "g0"
    assert len(slot(r, "quick")) == 3 and len(slot(r, "radar")) == 3
    assert r["hook"] == (deep + slot(r, "quick"))[:3]


def test_deep_flexes_to_four_on_a_strong_week_and_to_two_on_a_thin_one():
    strong = [st(f"g{n}", "global", d=3, r=3, e=3, t=2) for n in range(3)] + [st("reg", "regional", d=3, r=3, e=3, t=3)]
    assert len(slot(ranked(strong), "deep")) == 4
    thin = [st("g", "global", d=3, r=2), st("reg", "regional", d=3, r=3)] + [st(f"w{n}", d=1, r=1, e=1, t=0) for n in range(4)]
    r = ranked(thin)
    assert slot(r, "deep") == ["reg", "g"] and len(slot(r, "quick")) == 3


def test_africa_and_turkiye_keep_their_seat():
    pairs = [st(f"g{n}", "global", d=3, r=2) for n in range(8)] + [st("reg", "regional", d=3, r=3)] + \
            [st("tr", "regional", d=1, r=1, e=1, t=0, regions=["turkey"]),
             st("af", "regional", d=1, r=1, e=1, t=0, regions=["africa"], depth=False)]
    r = ranked(pairs)
    by = {s["id"]: s for s in r["stories"]}
    assert by["tr"]["slot"] in ("quick", "radar") and by["af"]["slot"] == "radar"
    assert len(slot(r, "quick")) == 3 and len(slot(r, "radar")) == 3


def test_generic_explainers_go_to_shorts_never_the_episode():
    idea = {"job": "explainer", "fact": "An agent is software that takes actions for you.",
            "implication": "Your vendor will sell it by the task.", "question": "Who signs off on what it does?"}
    r = ranked([st("exp", "explainer", d=3, r=3, e=3, t=3, short=idea), st("g", "global", d=3), st("reg", "regional", d=3)])
    by = {s["id"]: s for s in r["stories"]}
    assert by["exp"]["slot"] == "short" and "exp" not in r["hook"]
    assert [c["story_id"] for c in r["shorts"]] == ["exp"]


# ── 5. Shorts candidates ─────────────────────────────────────────────────────
def test_shorts_need_fact_implication_question_and_no_invented_number():
    full = {"job": "breaking", "fact": "G42 opened a 5 gigawatt campus.", "implication": "Capacity moves to Abu Dhabi.",
            "question": "Where will your workloads run?"}
    pairs = [st("a", d=3, short=full, text="G42 opened a 5 gigawatt campus in Abu Dhabi", hours=5),
             st("b", d=3, short={**full, "question": ""}),
             st("c", d=3, short={**full, "fact": "G42 spent $90 billion."}, text="G42 opened a campus"),
             st("d", d=3, short=dict(full), text="G42 opened a 5 gigawatt campus", hours=24 * 5)]
    r = ranked(pairs)
    got = {c["story_id"]: c for c in r["shorts"]}
    assert set(got) == {"a", "d"}
    assert got["a"]["job"] == "breaking" and got["d"]["job"] != "breaking"      # five days old is not breaking
    assert all(c["fact"] and c["implication"] and c["question"] for c in r["shorts"])


# ── 6. founder decisions ─────────────────────────────────────────────────────
def test_a_decision_moves_a_story_and_is_logged_with_its_reason():
    r = ranked([st(f"g{n}", "global", d=3, r=2, t=3 - n) for n in range(4)] + [st("reg", "regional", d=3, r=3),
                st("low", d=1, r=1, e=1, t=0)])
    rank.approve(r, "founder", NOW)
    rank.decide(r, "LOW", "deep", "The Jordan angle matters to our viewers", "founder", CFG, now=NOW)
    by = {s["id"]: s for s in r["stories"]}
    assert by["low"]["slot"] == "deep" and by["low"]["override"] == "deep"
    assert r["overrides"][-1] == {"story_id": "low", "title": "Story low", "action": "deep", "by": "founder",
                                  "reason": "The Jordan angle matters to our viewers", "at": NOW.isoformat()}
    assert r["approved"] is None                                   # a change after approval needs a new approval
    rank.decide(r, "g0", "drop", "Covered it in the breaking Short", "founder", CFG, now=NOW)
    assert {s["id"]: s for s in r["stories"]}["g0"]["slot"] == "out" and "g0" not in r["hook"]
    rank.decide(r, "g0", "auto", "changed my mind", "founder", CFG, now=NOW)
    assert {s["id"]: s for s in r["stories"]}["g0"]["slot"] == "deep" and len(r["overrides"]) == 3
    for bad in (("nope", "deep", "x"), ("low", "deep", "  "), ("low", "headline", "x")):
        with pytest.raises(ValueError):
            rank.decide(r, *bad, "founder", CFG, now=NOW)


def test_story_comment_parsing():
    import story_comment as sc
    assert sc.parse("/story s1a2 deep because the Jordan angle matters\nthanks") == ("s1a2", "deep", "the Jordan angle matters")
    assert sc.parse("/story S1A2 drop: covered already") == ("s1a2", "drop", "covered already")
    assert sc.parse("/story approve") == ("", "approve", "")
    assert sc.parse("/story s1 quick because $(touch pwned)")[2] == "$(touch pwned)"      # stays text
    for bad in ("/story s1 deep", "/story s1 headline because x", "hello", "/story"):
        with pytest.raises(ValueError):
            sc.parse(bad)


def test_story_decide_workflow_is_owner_only_and_never_splices_the_comment():
    text = (ROOT / ".github/workflows/story-decide.yml").read_text(encoding="utf-8")
    wf = yaml.safe_load(text)
    job = wf["jobs"]["decide"]
    assert "github.event.comment.user.login == github.repository_owner" in job["if"]
    assert "startsWith(github.event.issue.title, 'Ranking:')" in job["if"]
    assert "eval " not in text
    for step in job["steps"]:
        body = step.get("run", "") + step.get("with", {}).get("script", "")
        assert "github.event.comment.body" not in body and "steps.apply.outputs" not in body, step.get("name")


def test_weekly_job_stops_at_the_ranking_until_it_is_approved():
    text = (ROOT / ".github/workflows/weekly.yml").read_text(encoding="utf-8")
    steps = {s.get("name"): s for s in yaml.safe_load(text)["jobs"]["script"]["steps"]}
    assert "Open ranking issue" in steps and "STAGE == 'ranking'" in steps["Open ranking issue"]["if"]
    assert "STAGE != 'ranking'" in steps["Open review issue"]["if"]
    assert "Ranking: " in steps["Open ranking issue"]["with"]["script"]
    # A ranking-only run has no script.md: its artifact must not be named week-<week> (the render takes the newest).
    assert "STAGE == 'ranking'" in text.split("actions/upload-artifact")[1].split("retention-days")[0]


def test_awaiting_approval_only_when_the_setting_asks_for_it():
    r = ranked([st("g", d=3), st("reg", "regional", d=3)])
    assert rank.awaiting_approval(r, CFG)
    assert not rank.awaiting_approval(r, {**CFG, "ranking": {"require_approval": False}})
    rank.approve(r, "founder", NOW)
    assert not rank.awaiting_approval(r, CFG) and r["approved"]["by"] == "founder"


# ── judge: model and deterministic fallback ──────────────────────────────────
def _stories():
    a = [item("Humain signs sovereign cloud contract with Aramco in Riyadh", s, region="gulf",
              summary="Saudi's Humain signed a 5 year sovereign cloud contract with Aramco. " * 6) for s in ("Reuters", "Arab News")]
    b = [item("OpenAI raises new funding round at higher valuation", "Some Blog", summary="funding")]
    return cl.cluster(a + b, CFG)


def test_without_an_api_key_the_fallback_is_deterministic(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    one = rank.build(_stories(), CFG, "2026-W48", now=NOW)
    two = rank.build(_stories(), CFG, "2026-W48", now=NOW)
    assert one["judge"] == "keyword fallback" and one == two
    top = one["stories"][0]
    assert "Humain" in top["title"] and top["slot"] in ("deep", "quick") and top["kind"] == "regional"
    assert all(set(s["scores"]) == set(rank.CRITERIA) for s in one["stories"])
    assert one["thesis"]


class FakeClient:
    def __init__(self, parsed):
        self.parsed, self.calls = parsed, []
        self.messages = self

    def parse(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(parsed_output=self.parsed, stop_reason="end_turn", usage=None)


def test_model_judge_scores_only_known_stories_and_sources_are_fenced():
    stories = _stories()
    sid = next(s["id"] for s in stories if "Humain" in s["title"])
    crit = jd.Criterion(score=3, reason="A named Saudi buyer changes vendor shortlists.")
    one = jd.StoryJudgement(story_id=sid, kind="regional", decision_impact=crit, regional_consequence=crit,
                            evidence=crit, tension=crit, regional_actor="Aramco", new_development=True, depth=True,
                            kill="none", decision_frame="buy_build_partner", short=None)
    ghost = one.model_copy(update={"story_id": "made-up"})
    client = FakeClient(jd.Judgement(stories=[one, ghost], thesis="Sovereign cloud contracts now have named Saudi buyers."))
    r = rank.build(stories, CFG, "2026-W48", client=client, now=NOW)
    assert r["judge"] == rank.opts(CFG)["model"] and "made-up" not in {s["id"] for s in r["stories"]}
    top = next(s for s in r["stories"] if s["id"] == sid)
    assert top["total"] == 21 and top["slot"] == "deep"
    other = next(s for s in r["stories"] if s["id"] != sid)
    assert other["judged_by"] == "keyword fallback"               # the model skipped it: scored in code, said so
    prompt = client.calls[0]["messages"][0]["content"]
    assert "<stories>" in prompt and "total" not in json.dumps(jd.Judgement.model_json_schema()).lower()
    assert "report" in client.calls[0]["system"].lower() and "instructions" in client.calls[0]["system"].lower()
    assert r["thesis"].startswith("Sovereign")


def test_a_thesis_with_a_number_not_in_the_sources_is_replaced():
    stories = _stories()
    client = FakeClient(jd.Judgement(stories=[], thesis="Gulf AI spending hit $400 billion this week."))
    r = rank.build(stories, CFG, "2026-W48", client=client, now=NOW)
    assert "400" not in r["thesis"] and r["thesis"]


# ── report, storage, and the hand-over to the script writer ──────────────────
def test_report_shows_scores_reasons_commands_and_the_log(tmp_path, monkeypatch):
    monkeypatch.setattr(rank, "DIR", tmp_path)
    r = ranked([st("g", d=3), st("reg", "regional", d=3), st("old", repeat=["covered headline"]),
                st("gone", repeat=["covered headline"])])
    rank.decide(r, "old", "radar", "worth one line", "founder", CFG, now=NOW)
    md = rank.to_md(r)
    for needle in ("/story", "approve", "decision_impact because", "worth one line", "| g |", "×3", "Out"):
        assert needle in md, needle
    rank.save(r)
    assert rank.load("2026-W48") == r and rank.load("2026-W48-en") == r and rank.load("2026-W49") is None


def test_script_writer_gets_only_the_slotted_stories_in_the_approved_order():
    from pipeline.scripting.script_engine import EditorialPlan, Segment
    a, b, c = (item(f"{w} story headline", "Reuters") for w in ("alpha", "bravo", "charlie"))
    r = ranked([st("g", d=3, items=[a.to_dict()]), st("reg", "regional", d=3, r=3, items=[b.to_dict()]),
                st("old", repeat=["x"], items=[c.to_dict()])])
    assert {i.id for i in rank.slotted_items(r)} == {a.id, b.id}
    brief = rank.brief(r, CFG)
    assert brief.index("Story reg") < brief.index("Story g") and "Story old" not in brief
    assert "what to ask or watch next" in brief and "30" in brief and "investment" in brief
    seg = lambda i: Segment(track="models", item_ids=[i.id], headline_en="h", angle="a", enterprise_impact="e",
                            broll_ideas=[], approx_seconds=90)
    plan = EditorialPlan(episode_title_ar="ع", cold_open_hook_en="h", segments=[seg(a), seg(b)],
                         quick_fire_item_ids=[], thumbnail_text_ar="ع")
    missing = rank.align_plan(plan, r)
    assert [s.story_id for s in plan.segments] == ["reg", "g"] and missing == []
    plan.segments = plan.segments[:1]
    assert rank.align_plan(plan, r) == ["g"]


def test_settings_document_the_ranking_and_keep_the_region_seats():
    cfg = yaml.safe_load((ROOT / "config/settings.yaml").read_text(encoding="utf-8"))
    rk = cfg["ranking"]
    assert rk["weights"] == {"decision_impact": 3, "regional_consequence": 2, "evidence": 1, "tension": 1}
    assert (rk["deep"]["default"], rk["deep"]["min"], rk["deep"]["max"], rk["quick"], rk["radar"]) == (3, 2, 4, 3, 3)
    assert 15 <= rk["max_stories"] <= 20 and rk["require_approval"] is True
    assert cfg["scoring"]["min_per_region"] == {"africa": 1, "turkey": 1}
    assert rank.opts(cfg)["weights"] == rank.DEFAULTS["weights"]
