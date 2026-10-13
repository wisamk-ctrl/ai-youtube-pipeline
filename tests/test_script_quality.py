"""Script engine end to end with a mocked Claude: style guide injection, critic loop, source map."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import load_settings  # noqa: E402
from pipeline.models import NewsItem  # noqa: E402
from pipeline.scripting import source_map  # noqa: E402
from pipeline.scripting import critic as critic_mod  # noqa: E402
from pipeline.scripting.critic import Critique, Defect, Fix, fixes_as_instruction  # noqa: E402
from pipeline.scripting.script_engine import EditorialPlan, ScriptEngine, Segment  # noqa: E402
from pipeline.scripting.source_map import Attribution, SourceMap  # noqa: E402

ITEM = NewsItem("CNBC", "rss", "Mistral unveils Large 4", "Mistral launched Large 4, an open-weight model.",
                "https://cnbc.com/mistral", datetime.now(timezone.utc))
PLAN = EditorialPlan(episode_title_ar="ع", cold_open_hook_en="h",
                     segments=[Segment(track="models", item_ids=[ITEM.id], headline_en="h", angle="a",
                                       enterprise_impact="e", broll_ideas=[], approx_seconds=60)],
                     quick_fire_item_ids=[], thumbnail_text_ar="ع")
SCRIPT = "[Section: الافتتاحية]\n" + "أعلنت ميسترال عن نموذج Large 4. " * 520 + "وهذا يهم شركات المنطقة. نلتقي الأسبوع المقبل."


class FakeClient:
    """Records every call; critic scores low once, then high; source map flags one unsourced claim."""

    def __init__(self):
        self.calls: list[dict] = []
        self.critic_calls = 0
        self.messages = NS(parse=self.parse)
        self.beta = NS(messages=NS(stream=self.stream))

    def parse(self, **kw):
        self.calls.append(kw)
        fmt = kw["output_format"]
        if fmt is EditorialPlan:
            return NS(stop_reason="end_turn", parsed_output=PLAN)
        if fmt is Critique:
            self.critic_calls += 1
            # Two samples per round (settings: samples 2). Round 1 (calls 1-2): hook has a major +
            # a minor defect in a one-segment script → computed 4, below the bar. Round 2 (calls 3-4): clean → 10.
            low = self.critic_calls <= 2
            defects = [Defect(axis="hook", severity="major", rule="no fact first", quote="أعلنت ميسترال"),
                       Defect(axis="hook", severity="minor", rule="first sentence long", quote="أعلنت ميسترال عن")] if low else []
            return NS(stop_reason="end_turn", parsed_output=Critique(
                hook=1 if low else 10, clarity=1 if low else 10, pacing=1 if low else 10, flow=1 if low else 10,
                arabic=1 if low else 10, value=1 if low else 10,   # with defects present, self-scores are ignored and recomputed
                defects=defects,
                worst_three=[Fix(where="أعلنت ميسترال", problem="opens with a company, not a stake", fix="open with the 40% price cut")],
                verdict="not yet" if low else "airable"))
        if fmt is SourceMap:
            n = len(source_map.sentences(SCRIPT))
            atts = [Attribution(n=i, kind="claim", item_ids=[ITEM.id], support="direct") for i in range(1, n - 1)]
            atts += [Attribution(n=n - 1, kind="claim", item_ids=["made-up-id"], support="none"),
                     Attribution(n=n, kind="transition", item_ids=[], support="none")]
            return NS(stop_reason="end_turn", parsed_output=SourceMap(sentences=atts))
        raise AssertionError(fmt)

    def stream(self, **kw):
        self.calls.append(kw)
        client = self

        class S:
            def __enter__(s): return s
            def __exit__(s, *a): pass
            def get_final_message(s): return NS(stop_reason="end_turn", model="m", content=[NS(type="text", text=SCRIPT)])
        return S()


def test_engine_runs_critic_loop_and_source_map():
    client = FakeClient()
    cfg = load_settings()
    cfg["scripting"]["critic"] = {"model": "x", "min_score": 8, "max_rounds": 2}
    result = ScriptEngine(cfg, client).run([ITEM], week_label="t")

    # style guide reached the writer and the reviewer
    systems = [c.get("system", "") for c in client.calls]
    assert sum("دليل أسلوب" in s for s in systems) >= 2
    # critic: round 1 hook 7 (one major + one minor, computed) → reviewer re-run with the fix → round 2 clean
    assert [r["minimum"] for r in result.critique_rounds] == [4, 10]   # one segment, pen 3 → 10-6
    assert result.critique_rounds[0]["scores"]["hook"] == 4 and result.critique_rounds[0]["stable"] is True
    assert len(result.critique_rounds[0]["samples"]) == 2 and client.critic_calls == 4
    reviewer_calls = [c for c in client.calls if "draft_script" in str(c.get("messages"))]
    assert any("open with the 40% price cut" in str(c["messages"]) for c in reviewer_calls)
    # source map: last claim had an invented id → stripped → unsourced
    assert result.source_stats == {"sentences": len(source_map.sentences(SCRIPT)), "claims": len(source_map.sentences(SCRIPT)) - 1, "unsourced": 1}
    assert "**1 unsourced claims**" in result.source_map_md and "Unsourced claims" in result.source_map_md
    assert "[CNBC](https://cnbc.com/mistral)" in result.source_map_md


def test_fix_instruction_is_explicit():
    c = Critique(hook=4, clarity=8, pacing=8, flow=8, arabic=8, value=8, verdict="v",
                 worst_three=[Fix(where="w", problem="p", fix="f")])
    text = fixes_as_instruction(c)
    assert "hook" in text and "1. At «w»: p → f" in text


def test_polish_applies_last_fixes_and_appends_round():
    client = FakeClient()
    cfg = load_settings()
    cfg["scripting"]["critic"] = {"model": "x", "min_score": 8, "max_rounds": 2}
    prior = [{"scores": {"hook": 5, "clarity": 9, "pacing": 8, "flow": 8, "arabic": 9, "value": 8}, "minimum": 5,
              "verdict": "not yet", "worst_three": [{"where": "أعلنت ميسترال", "problem": "p", "fix": "open with the 40% price cut"}]}]
    result = ScriptEngine(cfg, client).polish(PLAN, SCRIPT, [ITEM], prior)
    reviewer_calls = [c for c in client.calls if "draft_script" in str(c.get("messages"))]
    assert len(reviewer_calls) == 1 and "open with the 40% price cut" in str(reviewer_calls[0]["messages"])
    assert [r["minimum"] for r in result.critique_rounds] == [5, 4]   # new round: computed from defects
    assert result.source_stats["unsourced"] == 1


def test_score_does_not_rewrite():
    client = FakeClient()
    cfg = load_settings()
    result = ScriptEngine(cfg, client).score(PLAN, SCRIPT, [ITEM], [])
    assert result.script == SCRIPT
    assert not [c for c in client.calls if "draft_script" in str(c.get("messages"))]
    assert len(result.critique_rounds) == 1 and result.source_stats["claims"] >= 1


def test_scores_are_computed_from_defects():
    d = [Defect(axis="clarity", severity="major", rule="r", quote="q"),
         Defect(axis="clarity", severity="minor", rule="r", quote="q"),
         Defect(axis="value", severity="major", rule="r", quote="q")] + \
        [Defect(axis="pacing", severity="major", rule="r", quote="q")] * 6
    # one segment: raw density. clarity pen 3 → 10-6=4; pacing pen 12 → floor 1; value pen 2 → 6
    assert critic_mod.scores_from_defects(d, 1) == {"hook": 10, "clarity": 4, "pacing": 1, "flow": 10, "arabic": 10, "value": 6}
    # eight segments: the same list is a pattern, not a wall. clarity 10-round(0.75)=9; pacing 10-3=7; value 10-round(0.5)=10
    assert critic_mod.scores_from_defects(d, 8) == {"hook": 10, "clarity": 9, "pacing": 7, "flow": 10, "arabic": 10, "value": 10}
    assert critic_mod.segment_count("[Section: a]\nx\n[Section: b]\ny") == 2 and critic_mod.segment_count("كلمة " * 400) == 3


def test_consensus_resamples_on_disagreement_and_takes_median():
    seq = iter([{"hook": 9}, {"hook": 6}, {"hook": 8}])   # samples disagree by 3 → third sample → median 8

    class C:
        def __init__(self): self.messages = NS(parse=self.parse)
        def parse(self, **kw):
            sc = {a: 9 for a in critic_mod.AXES} | next(seq)
            return NS(stop_reason="end_turn", parsed_output=Critique(**sc, worst_three=[Fix(where="w", problem="p", fix="f")], verdict="v"))

    final, samples, stable = critic_mod.consensus("s", "g", "rubric", {"samples": 2, "max_disagreement": 1}, "m", C())
    assert [s["hook"] for s in samples] == [9, 6, 8] and stable is False and final.hook == 8
    assert final.verdict == "v" and final.minimum == 8
