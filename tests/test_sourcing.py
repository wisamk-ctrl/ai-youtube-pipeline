"""Editorial sourcing (review 2026-11-07, Tier 1 #5-#8): radar names, radar never cited, publisher
tiers, full articles behind Google News, figures and attributions in the source map, the gate.
No network: every HTTP call is mocked."""

from __future__ import annotations

import base64
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingestion import articles  # noqa: E402
from pipeline.ingestion.publishers import is_radar, load_publishers, on_screen_ok  # noqa: E402
from pipeline.ingestion.scoring import score_item  # noqa: E402
from pipeline.ingestion.watchlist import load_watchlist  # noqa: E402
from pipeline.models import NewsItem  # noqa: E402
from pipeline.radar import radar  # noqa: E402
from pipeline.radar.extract import ItemTags, Mention  # noqa: E402
from pipeline.radar.signals import Signal  # noqa: E402
from pipeline.scripting import director, source_map  # noqa: E402
from pipeline.scripting.source_map import Attribution, SourceMap  # noqa: E402

W = load_watchlist()
NOW = datetime.now(timezone.utc)


def item(source: str, title: str, summary: str = "", url: str = "", days: float = 1) -> NewsItem:
    return NewsItem(source=source, source_type="rss", title=title, summary=summary,
                    url=url or f"https://{source.lower().replace(' ', '')}.example/{abs(hash(title))}",
                    published=NOW - timedelta(days=days))


def tags(i: NewsItem, name: str) -> ItemTags:
    return ItemTags(item_id=i.id, event="launch", region="cn",
                    mentions=[Mention(name=name, kind="org", track="models", role="subject")])


# ── 1. Radar knows watched names by contains-match ───────────────────────────
def test_tencent_counts_as_watched():
    terms = [t for e in W.entities for t in e.terms]
    assert radar.is_known("Tencent", terms)                 # alias, and contained in "Tencent Hunyuan"
    assert radar.is_known("Tencent Hy4", terms)
    assert radar.is_known("Hy4", terms)
    assert radar.is_known("TencentHunyuan", terms)          # glued spelling
    assert not radar.is_known("Armada", ["Arm"])            # whole words only
    assert radar.is_known("Arm Holdings", ["Arm"])

    a, b = item("Reuters", "Tencent ships Hy4"), item("CNBC", "Tencent's new model")
    cands = radar.build_candidates([a, b], {a.id: tags(a, "Tencent"), b.id: tags(b, "Tencent")},
                                   [Signal("tencent", "hf_trending", 0.9, "https://huggingface.co/tencent")], W)
    assert cands == {}


# ── 2. Radar is never a citable source ──────────────────────────────────────
def _radar_note() -> tuple[NewsItem, NewsItem, NewsItem]:
    a = item("Reuters", "Reflection AI releases Beam", days=5)
    b = item("CNBC", "Reflection AI open model tops charts", days=2)
    cands = radar.build_candidates([a, b], {a.id: tags(a, "Reflection AI"), b.id: tags(b, "Reflection AI")},
                                   [Signal("reflectionai", "hf_trending", 0.9, "https://huggingface.co/r/beam")], W)
    note = radar.surface(cands, {}, {"radar": {}}, "2026-W45")[0]
    return note, a, b


def test_radar_note_carries_oldest_date_and_names_its_items():
    note, a, b = _radar_note()
    assert is_radar(note) and note.published == a.published          # not "now"
    assert a.id in note.summary and b.id in note.summary and "not a citable source" in note.summary


def test_radar_never_reaches_the_source_map_or_the_screen():
    note, a, _ = _radar_note()
    seen = {}

    def parse(**kw):
        seen["content"] = kw["messages"][0]["content"]
        out = SourceMap(sentences=[Attribution(n=1, kind="claim", item_ids=[note.id], support="direct")])
        return SimpleNamespace(stop_reason="end_turn", parsed_output=out, usage=None)

    sents, smap = source_map.build("ريفلكشن أطلقت نموذج Beam.", [note, a], "m",
                                   SimpleNamespace(messages=SimpleNamespace(parse=parse)))
    assert note.id not in seen["content"] and a.id in seen["content"]
    assert smap.sentences[0].item_ids == [] and source_map.stats(smap)["unsourced"] == 1

    assert note.id not in director._items_block([note, a]) and a.id in director._items_block([note, a])
    script = "مرحبا فيكم.\n"
    problems = director.check(script, f"[Visual: source {note.id}]\n{script}", [note, a])
    assert any("not creditable" in p for p in problems)


# ── 3. Publisher tiers ──────────────────────────────────────────────────────
def test_publisher_tiers_and_weights():
    pubs = load_publishers()
    assert pubs.tier(item("Reuters", "x")) == "A"
    assert pubs.tier(item("Anything", "x", url="https://www.reuters.com/tech/x")) == "A"   # by domain
    assert pubs.tier(item("OpenAI", "x", url="https://openai.com/index/x")) == "A"          # newsroom
    assert pubs.tier(item("TechCrunch", "x")) == "B"
    assert pubs.tier(item("TLDR AI", "x")) == "C"
    assert pubs.tier(item("shattered.io", "x")) == "C"                                       # unknown
    assert pubs.tier(item("Google News · Anthropic", "x", url="https://news.google.com/rss/articles/a")) == "C"

    title = "OpenAI launches enterprise agents API"
    wire = score_item(item("Reuters", title), NOW)
    blog = score_item(item("shattered.io", title), NOW)
    assert wire.score_breakdown["publisher_tier"] == 1.3 and blog.score_breakdown["publisher_tier"] == 0.6
    assert wire.score / blog.score == pytest.approx(1.3 / 0.6, rel=0.01)


def test_tier_c_is_never_the_on_screen_credit():
    wire, agg = item("Reuters", "G42 opens Greek AI factory"), item("shattered.io", "G42 opens Greek AI factory!")
    assert on_screen_ok(wire) and not on_screen_ok(agg)
    assert agg.id not in director._items_block([wire, agg])
    script = "مرحبا فيكم.\n"
    assert any("not creditable" in p for p in director.check(script, f"[Visual: source {agg.id}]\n{script}", [wire, agg]))
    assert not director.check(script, f"[Visual: source {wire.id}]\n{script}", [wire, agg])


# ── 4. Full articles behind Google News, syndication counted once ───────────
class Resp:
    def __init__(self, text: str = "", status: int = 200):
        self.text, self.status_code = text, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


ARTICLE = ("<html><nav><p>Home News Tech Markets and more navigation links here</p></nav><article>"
           "<p>Mistral said on Tuesday it raised 1.7 billion euros in a round led by ASML, valuing it at 11.7 billion.</p>"
           "<p>The Paris-based lab will use the money for compute, according to the statement seen by Reuters.</p>"
           "<script>var x = 1;</script></article><footer><p>Copyright notice and other footer boilerplate text</p></footer></html>")


def _gn_link(target: str) -> str:
    raw = b"\x08\x13\x22" + bytes([len(target)]) + target.encode() + b"\xd2\x01\x00"
    return "https://news.google.com/rss/articles/" + base64.urlsafe_b64encode(raw).decode().rstrip("=")


def test_readability_keeps_article_paragraphs_only():
    text = articles.extract_text(ARTICLE)
    assert "1.7 billion euros" in text and "navigation" not in text and "footer" not in text and "var x" not in text


def test_google_news_item_gets_publisher_url_and_article_text(monkeypatch):
    target = "https://www.reuters.com/technology/mistral-raises-2026-11-04/"
    gn = item("Reuters", "Mistral raises funds", url=_gn_link(target))
    gets = []
    monkeypatch.setattr(articles.requests, "get", lambda url, **kw: gets.append(url) or Resp(ARTICLE))
    assert articles.resolve_google_news(gn.url, 5) == target
    assert articles.enrich([gn], {"enabled": True, "max_items": 5}) == 1
    assert gn.url == target and "1.7 billion euros" in gn.summary and gets == [target]


def test_article_fetch_failures_keep_the_headline_and_respect_the_cap(monkeypatch):
    items = [item("Reuters", f"Story {n}", summary="headline only", url=_gn_link(f"https://reuters.com/{n}"))
             for n in range(4)]
    gets = []

    def boom(url, **kw):
        gets.append(url)
        raise TimeoutError("slow site")

    monkeypatch.setattr(articles.requests, "get", boom)
    assert articles.enrich(items, {"enabled": True, "max_items": 2}) == 0
    assert all(i.summary == "headline only" for i in items) and len(gets) == 2
    assert articles.enrich(items, {"enabled": False}) == 0 and len(gets) == 2   # off → no request at all


def test_syndicated_copies_count_once():
    wire = item("Reuters", "Nvidia to invest $2 billion in Saudi AI venture", summary="x" * 50)
    copy1 = item("shattered.io", "Nvidia to invest $2 billion in Saudi AI venture - report", summary="x" * 900)
    copy2 = item("Zawya", "Nvidia to invest $2 bln in Saudi AI venture")
    other = item("CNBC", "Humain signs chip deal with AMD")
    kept = articles.collapse_syndicated([copy1, wire, copy2, other])
    assert [k.source for k in kept] == ["Reuters", "CNBC"]          # best-tier copy kept, order preserved

    # The radar counts a syndicated wire story as one source.
    cands = radar.build_candidates([wire, copy1], {wire.id: tags(wire, "Arcee"), copy1.id: tags(copy1, "Arcee")}, [], W)
    assert len(cands["arcee"].sources) == 1


def test_lead_only_channels_never_reach_the_script():
    from pipeline.config import load_settings
    from pipeline.ingestion.youtube_ingest import is_lead_only
    cfg = load_settings()
    hype = NewsItem("TheAIGRID", "youtube", "AGI is here!!", "", "https://youtube.com/watch?v=1", NOW)
    calm = NewsItem("AI Explained", "youtube", "Gemini 3 paper, read closely", "", "https://youtube.com/watch?v=2", NOW)
    assert is_lead_only(hype, cfg) and not is_lead_only(calm, cfg)


# ── 5. Source map: figures, attributions, partial, gate ─────────────────────
def test_claim_figures_normalise_digits_and_spoken_numbers():
    assert source_map.claim_figures("رفعت ٣٫٥ مليار دولار و 1,200 موظف") == ["3.5", "1200"]
    assert source_map.claim_figures("البنك بيوفّر ستين بالمية من التكلفة") == ["60"]
    assert source_map.claim_figures("خمسة وعشرين مليون مستخدم") == ["25"]
    assert source_map.claim_figures("ولا واحد توقّع هالشي") == []      # «واحد» alone is not a figure


def _verified(sentence: str, it: NewsItem, support: str = "direct") -> Attribution:
    smap = SourceMap(sentences=[Attribution(n=1, kind="claim", item_ids=[it.id], support=support)])
    source_map.verify([sentence], smap, [it])
    return smap.sentences[0]


def test_figures_must_appear_in_the_cited_item():
    it = item("Reuters", "Bank cuts AI costs", "The bank serves answers at sixty percent of the cost, "
              "after a $3.5 billion investment in 2026.")
    assert _verified("البنك بيوفّر ستين بالمية من التكلفة.", it).support == "direct"
    assert _verified("استثمروا ٣٫٥ مليار دولار.", it).support == "direct"
    a = _verified("استثمروا تلات مليارات وسبعين مليون دولار.", it)
    assert a.support == "none" and "figure" in a._problems[0]
    assert _verified("البنك وفّر 75% من التكلفة.", it).support == "none"


def test_named_attribution_must_match_the_publisher():
    reuters = item("Reuters", "Mistral raises funds", "Mistral raised money, it said.")
    assert _verified("حسب رويترز، ميسترال جمعت تمويل.", reuters).support == "direct"
    blog = item("shattered.io", "Mistral raises funds", "Mistral raised money.")
    a = _verified("حسب رويترز، ميسترال جمعت تمويل.", blog)
    assert a.support == "none" and "Reuters" in a._problems[0]
    relay = item("TLDR AI", "Mistral raises funds", "Mistral raised money, Reuters reported.")
    assert _verified("حسب رويترز، ميسترال جمعت تمويل.", relay).support == "partial"


def test_partial_is_listed_apart_and_before_the_unsourced_list():
    it = item("Reuters", "Mistral launches Large 4", "Mistral launched Large 4.")
    sents = ["ميسترال أطلقت Large 4.", "يعني المنافسة رح تشتد.", "ميسترال وظفت 900 شخص."]
    smap = SourceMap(sentences=[Attribution(n=1, kind="claim", item_ids=[it.id], support="direct"),
                                Attribution(n=2, kind="claim", item_ids=[it.id], support="partial"),
                                Attribution(n=3, kind="claim", item_ids=[it.id], support="direct")])
    source_map.verify(sents, smap, [it])
    md = source_map.render_md(sents, smap, [it])
    assert "1 sourced · 1 partial · **1 unsourced claims**" in md
    assert md.index("## Partial support") < md.index("## ⚠️ Unsourced claims")
    count, lines = source_map.unsourced_in_md(md)
    assert count == 1 and len(lines) == 1 and "900" in lines[0] and "figure 900" in lines[0]


def test_gate_blocks_unsourced_unless_overridden(tmp_path, monkeypatch):
    monkeypatch.delenv("SOURCES_OVERRIDE", raising=False)
    out = tmp_path / "output" / "2026-W46"
    out.mkdir(parents=True)
    ok, msg = source_map.gate(out, root=tmp_path)
    assert ok and "not audited" in msg                                # no map: warn, never block
    (out / "source_map.md").write_text("# Source map\n\n3 claims · **0 unsourced claims**\n", encoding="utf-8")
    assert source_map.gate(out, root=tmp_path)[0]
    (out / "source_map.md").write_text(
        "# Source map\n\n3 claims · **1 unsourced claims**\n\n## ⚠️ Unsourced claims — fix before recording\n\n"
        "- (3) ميسترال وظفت 900 شخص. — figure 900 not in the cited item(s)\n\n| # | sentence |\n", encoding="utf-8")
    ok, msg = source_map.gate(out, root=tmp_path)
    assert not ok and "(3) ميسترال وظفت 900 شخص." in msg and "sources_ok.txt" in msg
    monkeypatch.setenv("SOURCES_OVERRIDE", "1")
    assert source_map.gate(out, root=tmp_path)[0]
    monkeypatch.delenv("SOURCES_OVERRIDE")
    (tmp_path / "reviewed" / "2026-W46").mkdir(parents=True)
    (tmp_path / "reviewed" / "2026-W46" / "sources_ok.txt").write_text("checked by hand", encoding="utf-8")
    assert source_map.gate(out, root=tmp_path)[0]


def test_phase_video_and_import_refuse_on_unsourced(tmp_path, monkeypatch):
    import run_pipeline
    from pipeline.scripting import source_map as sm
    monkeypatch.delenv("SOURCES_OVERRIDE", raising=False)
    monkeypatch.setattr(sm, "gate", lambda out, root=None: (False, "Refusing: 1 unsourced claim(s)\n- (3) x"))
    out = tmp_path / "2026-W46"
    out.mkdir()
    (out / "script.md").write_text("مرحبا.\n", encoding="utf-8")
    with pytest.raises(SystemExit, match=r"(?s)phase video: Refusing.*\(3\) x"):
        run_pipeline.phase_video({}, out, dry_run=False, resume_id=None)
    with pytest.raises(SystemExit, match=r"phase import: Refusing"):
        run_pipeline.phase_import({}, out, "https://example.com/v.mp4")
