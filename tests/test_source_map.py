"""The source map must judge a script against the same source text the writer was given."""

from datetime import datetime, timezone
from types import SimpleNamespace

from pipeline.models import NewsItem
from pipeline.scripting import source_map


class CapturingClient:
    def __init__(self):
        self.content = ""
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kw):
        self.content = kw["messages"][0]["content"]
        out = source_map.SourceMap(sentences=[
            source_map.Attribution(n=1, kind="claim", item_ids=["x"], support="direct")])
        return SimpleNamespace(stop_reason="end_turn", parsed_output=out, usage=None)


def test_checker_sees_the_whole_body_the_writer_saw():
    # A long article whose key figure sits near the end, as NVIDIA and AWS blog posts do.
    body = ("Background paragraph. " * 100) + "The bank serves answers at sixty percent of the cost."
    assert len(body) > 2000
    item = NewsItem(source="NVIDIA", source_type="rss", title="Banks adopt open models",
                    summary=body, url="https://example.com/a", published=datetime.now(timezone.utc))
    client = CapturingClient()
    source_map.build("البنك بيشغّل مساعده بستين بالمية من التكلفة.", [item], "m", client)
    assert "sixty percent of the cost" in client.content
