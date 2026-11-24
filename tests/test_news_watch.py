from datetime import datetime, timezone

from pipeline.ingestion import news_watch
from pipeline.models import NewsItem

NOW = datetime(2026, 11, 13, 6, 0, tzinfo=timezone.utc)


def item(title, source, url):
    return NewsItem(source=source, source_type="rss", title=title, summary="text", url=url, published=NOW)


def test_an_outage_search_hit_is_flagged_once():
    state = {"items": {}, "runs": []}
    a = item("Microsoft outage hits Outlook and Teams worldwide", "Reuters", "https://r.example/1")
    flagged = news_watch.update(state, [a], {a.id}, {}, NOW)
    assert [f["title"] for f in flagged] == [a.title] and flagged[0]["why"] == "outage search"
    b = item("Microsoft outage hits Outlook and Teams around the world", "BBC", "https://b.example/2")
    assert news_watch.update(state, [a, b], {a.id, b.id}, {}, NOW) == []      # the same story, already told
    assert state["items"][b.id]["flagged"]


def test_a_story_many_outlets_carry_is_flagged_and_a_lone_one_is_not():
    state = {"items": {}, "runs": []}
    many = [item("OpenAI launches a wallet for its agents", s, f"https://x.example/{n}") for n, s in enumerate("ABCD")]
    lone = item("A small startup renames its product", "Blog", "https://y.example/1")
    flagged = news_watch.update(state, many + [lone], set(), {"news_watch": {"min_publishers": 4}}, NOW)
    assert len(flagged) == 1 and flagged[0]["outlets"] == ["A", "B", "C", "D"]


def test_kept_items_come_back_for_the_weekly_collection(tmp_path):
    state = {"items": {}, "runs": []}
    a = item("Microsoft outage", "Reuters", "https://r.example/1")
    news_watch.update(state, [a], set(), {}, NOW)
    news_watch.save(state, tmp_path / "w.json")
    assert [i.url for i in news_watch.kept_items(NOW, tmp_path / "w.json")] == [a.url]


def test_the_big_deals_search_is_collected_but_only_flagged_when_many_outlets_carry_it(monkeypatch):
    """2026-11-24: CrowdStrike's $43.9 billion purchase of Zscaler never reached the watch from the big outlets,
    because neither company is a watched name. A search for big deals that bear on AI brings such stories in; it
    is searched without the added "AI" word like the outage search, but a deal is flagged by the usual rule
    (several outlets), not on sight, so one stock-tip headline with "billion" in it does not raise an alert."""
    import yaml
    from pathlib import Path
    from pipeline.ingestion import watch_sources, rss_ingest, watchlist
    cfg = yaml.safe_load((Path(__file__).resolve().parent.parent / "config" / "settings.yaml").read_text(encoding="utf-8"))
    deals = [s for s in cfg["ingestion"]["google_news_sites"] if s["name"] == "Big deals"]
    assert len(deals) == 1 and deals[0]["raw"] is True and deals[0]["always_flag"] is False
    words = deals[0]["query"].lower().replace("(", " ").replace(")", " ").replace('"', " ").split()
    assert "billion" in words and "ai" in words and "acquisition" in words and "merger" in words
    asked = []

    def fake_sites(c):
        names = [s["name"] for s in c["ingestion"]["google_news_sites"]]
        asked.append(names)
        return [item(f"{n} headline", n, f"https://x.example/{n.replace(' ', '-')}") for n in names]
    monkeypatch.setattr(watch_sources, "fetch_site_queries", fake_sites)
    monkeypatch.setattr(watch_sources, "fetch_google_news", lambda *a, **k: [])
    monkeypatch.setattr(rss_ingest, "fetch_all_feeds", lambda c: [])
    found, urgent = news_watch.collect(cfg)
    always, rest = asked
    assert "Cloud outages" in always and "Big deals" not in always and "Big deals" in rest
    by_source = {i.source: i.id for i in found}
    assert by_source["Cloud outages"] in urgent and by_source["Big deals"] not in urgent


def test_the_headlines_the_big_deals_search_returned_flag_the_deal_we_missed():
    """The ten headlines Google News returned for the Big deals query on 2026-11-24, as they were. Four outlets
    told the CrowdStrike story closely enough to be one story, so the usual rule flags it; the others wait."""
    rows = [("Industrial Cyber", "CrowdStrike to acquire Zscaler in $43.9 billion all-stock deal to expand Zero Trust security and AI protection"),
            ("The Media Line", "Amazon To Acquire Israeli AI Startup Decart’s Technology in Deal Valued at $7.5 Billion"),
            ("The Jerusalem Post", "CrowdStrike to acquire Zscaler for $43.9 billion in AI cybersecurity megadeal"),
            ("Bloomberg", "Amazon Is Said to Pay $7.5 Billion For AI Startup Decart’s Tech"),
            ("Cybersecurity Dive", "CrowdStrike to acquire Zscaler for $43.9 billion amid turbulent threat environment"),
            ("The Fast Mode", "Marvell to Acquire Lumentum in $115 Billion AI Optical Connectivity Deal"),
            ("Techzine Global", "Amazon acquires Decart’s AI optimization technology"),
            ("Federal News Network", "CrowdStrike to acquire Zscaler in a $44 billion deal that would create a cybersecurity giant"),
            ("Forbes", "What CrowdStrike’s $43.9 Billion Zscaler Acquisition Means For Buyers"),
            ("Haaretz", "Amazon to buy Israeli startup Decart's AI tech in record $7.5 billion deal")]
    items = [item(title, source, f"https://x.example/{n}") for n, (source, title) in enumerate(rows)]
    flagged = news_watch.update({"items": {}, "runs": []}, items, set(), {"news_watch": {"min_publishers": 4}}, NOW)
    assert len(flagged) == 1 and "CrowdStrike" in flagged[0]["title"] and len(flagged[0]["outlets"]) == 4
