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
