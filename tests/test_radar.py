"""Radar: candidate building, threshold, state memory, ignore list. No network, no API key."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingestion.watchlist import load_watchlist  # noqa: E402
from pipeline.models import NewsItem  # noqa: E402
from pipeline.radar import radar  # noqa: E402
from pipeline.radar.extract import ItemTags, Mention  # noqa: E402
from pipeline.radar.signals import Signal  # noqa: E402

W = load_watchlist()
CFG = {"radar": {"min_sources": 2, "min_signals": 1, "max_surfaced": 3}}


def item(source: str, title: str) -> NewsItem:
    return NewsItem(source=source, source_type="rss", title=title, summary="", url=f"https://{source}/{abs(hash(title))}",
                    published=datetime.now(timezone.utc))


def tags(i: NewsItem, *names: str, role="subject", track="models", event="launch") -> ItemTags:
    return ItemTags(item_id=i.id, event=event, region="us",
                    mentions=[Mention(name=n, kind="org", track=track, role=role) for n in names])


def test_unknown_subject_with_two_sources_and_a_signal_clears_the_bar():
    a, b = item("cnbc.com", "Reflection AI releases Beam"), item("theverge.com", "Reflection AI's open model")
    t = {a.id: tags(a, "Reflection AI"), b.id: tags(b, "Reflection AI")}
    sig = [Signal("reflectionai", "hf_trending", 0.9, "https://huggingface.co/reflectionai/beam", "#5 trending")]
    cands = radar.build_candidates([a, b], t, sig, W)
    assert "reflection" in cands                                   # "ai" suffix stripped by norm()
    c = cands["reflection"]
    assert len(c.sources) == 2 and len(c.signals) == 1 and c.clears(2, 1)
    surfaced = radar.surface(cands, {}, CFG, "2026-W41")
    assert len(surfaced) == 1 and surfaced[0].track == "radar" and "Reflection AI" in surfaced[0].title


def test_watchlist_names_and_passing_mentions_are_not_candidates():
    a = item("cnbc.com", "Mistral partners with TypeSafe AI")
    t = {a.id: tags(a, "Mistral", "TypeSafe AI")}
    cands = radar.build_candidates([a], t, [], W)
    assert "mistral" not in cands and "typesafe" in cands            # Mistral is on the watchlist
    b = item("ft.com", "Column mentions Jev in passing")
    t2 = {b.id: tags(b, "TypeSafe AI", role="mentioned")}
    assert radar.build_candidates([b], t2, [], W) == {}


def test_one_source_is_not_enough_and_ignored_stays_hidden():
    a = item("cnbc.com", "Nous Research raises $90M")
    cands = radar.build_candidates([a], {a.id: tags(a, "Nous Research", event="funding")},
                                   [Signal("NousResearch", "hf_trending", 0.5, "https://hf.co/x")], W)
    assert not radar.surface(cands, {}, CFG, "w")
    b = item("reuters.com", "Nous Research's new model")
    cands = radar.build_candidates([a, b], {a.id: tags(a, "Nous Research"), b.id: tags(b, "Nous Research")},
                                   [Signal("NousResearch", "hf_trending", 0.5, "https://hf.co/x")], W)
    assert radar.surface(cands, {}, CFG, "w")
    state = {radar.norm("Nous Research"): {"status": "ignored", "weeks": {}}}
    assert not radar.surface(cands, state, CFG, "w")


def test_state_accumulates_weeks(tmp_path, monkeypatch):
    monkeypatch.setattr(radar, "STATE_PATH", tmp_path / "radar_state.json")
    a = item("cnbc.com", "Arena raises $200M")
    cands = radar.build_candidates([a], {a.id: tags(a, "Arena", event="funding")}, [], W)
    state = radar.load_state()
    radar.update_state(state, cands, "2026-W41"); radar.save_state(state)
    radar.update_state(state, cands, "2026-W42"); radar.save_state(state)
    again = radar.load_state()
    assert again["arena"]["status"] == "candidate" and set(again["arena"]["weeks"]) == {"2026-W41", "2026-W42"}
    assert "Arena" in radar.report_md(cands, again, CFG)


def test_ollama_provider_posts_schema_and_parses(monkeypatch):
    """The Ollama path sends our JSON schema as `format` and validates what comes back."""
    from pipeline.radar import extract as ex

    a = item("cnbc.com", "Reflection AI releases Beam")
    sent: dict = {}

    class Resp:
        def raise_for_status(self): pass
        def json(self):
            return {"message": {"content": '{"items": [{"item_id": "%s", "event": "launch", "region": "us", '
                    '"mentions": [{"name": "Reflection AI", "kind": "org", "track": "models", "role": "subject"}]}]}' % a.id}}

    def fake_post(url, json, timeout):
        sent.update(url=url, body=json)
        return Resp()

    monkeypatch.setattr(ex.requests, "post", fake_post)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    tags = ex.extract([a], opts={"provider": "ollama", "ollama_model": "qwen2.5", "ollama_url": "http://localhost:11434"})
    assert sent["url"] == "http://localhost:11434/api/chat" and sent["body"]["model"] == "qwen2.5"
    assert sent["body"]["format"]["properties"]["items"] and sent["body"]["stream"] is False
    assert tags[a.id].mentions[0].name == "Reflection AI" and tags[a.id].event == "launch"


def test_ollama_bad_json_is_skipped_not_fatal(monkeypatch):
    from pipeline.radar import extract as ex

    a = item("cnbc.com", "Something")

    class Resp:
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": "not json"}}

    monkeypatch.setattr(ex.requests, "post", lambda url, json, timeout: Resp())
    assert ex.extract([a], opts={"provider": "ollama"}) == {}
