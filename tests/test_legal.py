"""Legal-risk flags (pipeline/scripting/legal.py). Founder 2026-11-20: "anything that puts us at legal risk, we need
to highlight." W47's review found a breach blamed on a named company (Fireworks AI) on one minor security blog."""
from datetime import datetime, timezone

from pipeline.models import NewsItem
from pipeline.scripting import legal


def item(url, source="Reuters"):
    return NewsItem(source=source, source_type="rss", title="t", summary="", url=url, published=datetime.now(timezone.utc))


def smap(*rows):
    head = "# Source map\n\n| # | sentence | kind | support | sources |\n|---|---|---|---|---|\n"
    return head + "\n".join(f"| {n} | {s} | claim | {sup} | {src} |" for n, s, sup, src in rows) + "\n"


BLOG = "[GBHackers News](https://gbhackers.com/x)"
REUTERS = "[Reuters](https://reuters.com/a)"
GUARDIAN = "[The Guardian](https://theguardian.com/b)"
ITEMS = [item("https://gbhackers.com/x", "GBHackers News"), item("https://reuters.com/a"),
         item("https://theguardian.com/b", "The Guardian")]


def majors(flags):
    return [f for f in flags if f.severity == "major"]


def test_an_allegation_on_one_weak_source_is_major():
    md = smap((7, "وحسب موقع أخبار أمنية، السبب هجوم على مزوّد اسمه فايروركس{Fireworks AI} أدى لاختراق.", "direct", BLOG))
    flags = legal.check(md, ITEMS)
    assert [(f.n, f.rule) for f in majors(flags)] == [(7, "allegation")]


def test_an_allegation_on_one_wire_source_is_a_check_not_a_block():
    md = smap((3, "According to The Guardian, California has sued OpenAI.", "direct", GUARDIAN))
    flags = legal.check(md, ITEMS)
    assert not majors(flags) and [f.rule for f in flags] == ["allegation"]


def test_an_allegation_on_two_outlets_passes():
    md = smap((3, "California has sued OpenAI.", "direct", f"{GUARDIAN}; {REUTERS}"))
    assert legal.check(md, ITEMS) == []


def test_investment_advice_is_major_but_reporting_a_price_is_not():
    md = smap((1, "Now is the time to buy Anthropic stock.", "none", ""),
              (2, "اشتروا السهم قبل ما يطلع.", "none", ""),
              (3, "The stock closed up 17% on its first day.", "direct", REUTERS))
    assert [f.n for f in majors(legal.check(md, ITEMS))] == [1, 2]


def test_rulers_or_religion_next_to_a_negative_claim_is_major():
    md = smap((4, "ولي العهد انتقد الخطة وفشلت.", "direct", REUTERS),
              (5, "The crown prince opened the forum.", "direct", REUTERS))
    assert [(f.n, f.rule) for f in majors(legal.check(md, ITEMS))] == [(4, "sensitive")]


def test_a_quote_without_direct_support_is_major():
    md = smap((9, "وقال إنه الذكاء الاصطناعي ممكن يصير زي «مهاجم بمستوى دولة».", "partial", REUTERS),
              (10, "He called it a «perfect storm».", "direct", REUTERS))
    assert [(f.n, f.rule) for f in majors(legal.check(md, ITEMS))] == [(9, "quote")]


def test_markdown_lists_flags_and_the_count_reads_back():
    md = smap((7, "Hackers breached Acme, a blog says.", "direct", BLOG))
    out = legal.render_md(legal.check(md, ITEMS))
    assert "**1 major legal flag(s)**" in out and "- (7) [major] allegation" in out
    assert legal.majors_in_md(out) == (1, ["(7)"])
    assert "No legal flags" in legal.render_md([])


def test_gate_refuses_until_each_major_is_answered(tmp_path):
    out = tmp_path / "output" / "2026-W48"
    out.mkdir(parents=True)
    (out / "legal.md").write_text(legal.render_md(legal.check(smap((7, "Hackers breached Acme.", "direct", BLOG)), ITEMS)))
    ok, msg = legal.gate(out, root=tmp_path)
    assert not ok and "(7)" in msg
    note = tmp_path / "reviewed" / "2026-W48" / "legal_ok.txt"
    note.parent.mkdir(parents=True)
    note.write_text("(7) checked with a second source: The Verge confirms the breach.")
    assert legal.gate(out, root=tmp_path)[0]
    assert legal.gate(tmp_path / "output" / "none", root=tmp_path)[0]          # no legal.md: older weeks pass


def test_only_claims_are_checked_for_quotes():
    """The first real run flagged the show's own name in «» in the greeting, and scare quotes in a question."""
    head = "| # | sentence | kind | support | sources |\n|---|---|---|---|---|\n"
    md = head + "| 5 | أهلا فيكم بـ«أسبوع الذكاء الاصطناعي»، معكم وسام. | greeting | none |  |\n" \
                "| 6 | Who decides what \"out of control\" means? | question | none |  |\n"
    assert legal.check(md, ITEMS) == []


def test_a_short_name_in_quotation_marks_is_a_check_not_a_block():
    """W47-en: SDAIA's «Year of AI» programme name was blocked as an unsupported quote."""
    md = smap((53, 'SDAIA launched a "Year of AI" initiative across universities.', "partial", REUTERS))
    flags = legal.check(md, ITEMS)
    assert not majors(flags) and [f.rule for f in flags] == ["quote"]
