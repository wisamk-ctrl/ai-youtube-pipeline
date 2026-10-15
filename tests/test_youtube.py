"""YouTube channel ingestion, offline: handle resolution from page HTML, Atom parsing, cache."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingestion import youtube_ingest as yt  # noqa: E402

NOW = datetime.now(timezone.utc)
ATOM = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
 <title>AI Explained</title>
 <entry><id>yt:video:abc</id><title>GPT-6 tested: what changed</title><link rel="alternate" href="https://www.youtube.com/watch?v=abc"/>
  <author><name>AI Explained</name></author><published>{(NOW - timedelta(days=2)).isoformat()}</published>
  <media:group><media:description>A look at &lt;b&gt;benchmarks&lt;/b&gt; and agent use.</media:description></media:group></entry>
 <entry><id>yt:video:old</id><title>Old video</title><link rel="alternate" href="https://www.youtube.com/watch?v=old"/>
  <author><name>AI Explained</name></author><published>{(NOW - timedelta(days=40)).isoformat()}</published></entry>
</feed>"""


def test_parse_feed_keeps_window_and_marks_source_type():
    items = yt.parse_feed("AI Explained", ATOM.encode(), 0.9, NOW - timedelta(days=7), 5)
    assert [i.title for i in items] == ["GPT-6 tested: what changed"]
    i = items[0]
    assert i.source_type == "youtube" and i.source_weight == 0.9 and i.url.endswith("v=abc")
    assert "benchmarks" in i.summary and "<b>" not in i.summary


def test_handle_resolution_and_cache(tmp_path, monkeypatch):
    class R:
        text = '<html><script>{"responseContext":{},"channelId":"UCNJ1Ymd5yFuUPtn21xtRbbw","title":"x"}</script></html>'
        def raise_for_status(self): pass
    calls = []
    monkeypatch.setattr(yt.requests, "get", lambda url, **kw: calls.append(url) or R())
    cache = {}
    cid = yt.channel_id_for({"name": "AI Explained", "handle": "@aiexplained-official"}, cache, 5)
    assert cid == "UCNJ1Ymd5yFuUPtn21xtRbbw" and cache == {"aiexplained-official": cid}
    yt.channel_id_for({"name": "AI Explained", "handle": "aiexplained-official"}, cache, 5)
    assert len(calls) == 1                               # second lookup served from the cache
    assert yt.channel_id_for({"name": "x", "channel_id": "UCxxxxxxxxxxxxxxxxxxxxxx"}, cache, 5) == "UCxxxxxxxxxxxxxxxxxxxxxx"
    path = tmp_path / "c.json"
    yt.save_cache(cache, path)
    assert yt.load_cache(path) == cache and yt.load_cache(tmp_path / "missing.json") == {}
