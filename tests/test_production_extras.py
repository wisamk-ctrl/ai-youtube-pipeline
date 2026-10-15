"""Usage meter, tashkeel pass (mocked model), cue-card planning and SRT anchoring — all offline."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import usage  # noqa: E402
from pipeline.post import overlays  # noqa: E402
from pipeline.video import tashkeel  # noqa: E402

SCRIPT = """[Section: الافتتاحية]

أُعلن عن جولة تمويل بقيمة

[Pause]

ثلاثة مليارات دولار لشركة ميسترال Mistral.

[On-Screen Text: 3 مليارات دولار]

[Show B-Roll: Paris skyline]

وتريد الشركة أن تُدار نصف عملياتها بالذكاء الاصطناعي خلال عامين. نلتقي الأسبوع المقبل."""


def test_usage_meter_sums_per_model_and_prices_only_when_filled():
    usage.reset()
    usage.record("plan", "claude-opus-5-5", NS(input_tokens=1000, output_tokens=200))
    usage.record("critic", "claude-opus-5-5", NS(input_tokens=500, output_tokens=100, cache_read_input_tokens=50))
    usage.record("extract", "claude-haiku-5-5", NS(input_tokens=10, output_tokens=5))
    s = usage.summary()
    assert s["models"]["claude-opus-5-5"] == {"calls": 2, "input": 1550, "output": 300} and s["cost_usd"] is None
    priced = usage.summary({"claude-opus-5-5": {"input": 10, "output": 40}, "claude-haiku-5-5": {"input": 1, "output": 5}})
    assert priced["cost_usd"] == round(1550 / 1e6 * 10 + 300 / 1e6 * 40 + 10 / 1e6 * 1 + 5 / 1e6 * 5, 2)
    usage.reset()


def test_tashkeel_accepts_marks_only_and_rejects_word_changes():
    cfg = {"video": {"tashkeel_model": "m"}, "scripting": {"model": "x"}}
    marked = SCRIPT.replace("أُعلن", "أُعْلِنَ").replace("تُدار", "تُدَارَ")

    def client(text):
        return NS(messages=NS(parse=lambda **kw: NS(stop_reason="end_turn", usage=None, parsed_output=tashkeel.Vocalised(script=text))))

    out = tashkeel.vocalise(SCRIPT, cfg, client(marked))
    assert "تُدَارَ" in out and tashkeel.strip_harakat(out).split() == tashkeel.strip_harakat(SCRIPT).split()
    try:
        tashkeel.vocalise(SCRIPT, cfg, client(marked.replace("ثلاثة", "أربعة")))
        raise AssertionError("a changed word must be refused")
    except ValueError:
        pass


def test_cue_cards_are_planned_from_markers_and_anchored_to_srt(tmp_path):
    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:03,000\nأُعلن عن جولة تمويل بقيمة\n\n2\n00:00:03,000 --> 00:00:07,000\n"
                   "ثلاثة مليارات دولار لشركة ميسترال Mistral.\n\n", encoding="utf-8")
    cards = overlays.plan_cards(SCRIPT, 130, tmp_path, srt)
    assert [c.cue.kind for c in cards] == ["onscreen", "broll"]
    assert cards[0].cue.text == "3 مليارات دولار" and cards[0].seconds == 6.0 and cards[1].seconds == 4.0
    # the on-screen cue follows «…ميسترال Mistral.», which is subtitle 2 at t=3s: anchored there, not at the wpm estimate
    assert cards[0].at == 3.0
    assert cards[0].png.name == "card_01_onscreen.png"
