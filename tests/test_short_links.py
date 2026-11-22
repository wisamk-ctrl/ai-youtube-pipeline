"""Source links in the description are the publisher's own, cleaned address (founder 2026-11-22)."""
from pipeline.publish import description as d


def test_tracking_parameters_and_fragments_are_dropped():
    assert d.clean_url("https://x.com/a/b?utm_source=rss&utm_medium=feed&fbclid=1#top") == "https://x.com/a/b"


def test_parameters_that_identify_the_article_are_kept():
    assert d.clean_url("https://x.com/story?id=42&utm_campaign=z") == "https://x.com/story?id=42"


def test_a_google_news_link_becomes_the_publishers_link():
    g = "https://news.google.com/rss/articles/CBMi" + "A" * 240 + "?oc=5"
    out = d.short_sources([{"title": "T", "url": g}], resolve=lambda u, t: "https://outlet.com/news/1?utm_source=gn")
    assert out == [{"title": "T", "url": "https://outlet.com/news/1"}]


def test_an_unresolved_google_news_link_is_kept_so_the_source_still_traces():
    g = "https://news.google.com/rss/articles/CBMiXYZ?oc=5"
    assert d.short_sources([{"title": "T", "url": g}], resolve=lambda u, t: "")[0]["url"] == g


def test_other_links_are_not_sent_to_the_resolver():
    called = []
    d.short_sources([{"title": "T", "url": "https://x.com/a?ref=home"}], resolve=lambda u, t: called.append(u) or "")
    assert called == []


def test_the_description_writes_the_cleaned_link():
    text = d.build_description({}, [{"title": "T", "url": "https://x.com/a?utm_source=rss"}], {}, lang="en")
    assert "- T: https://x.com/a\n" in text and "utm_" not in text
