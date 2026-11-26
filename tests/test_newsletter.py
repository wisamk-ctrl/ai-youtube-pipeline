"""The weekly LinkedIn newsletter issue (pipeline/publish/newsletter.py, founder 2026-11-26)."""
import json
from types import SimpleNamespace

from pipeline.publish import newsletter as nl

SCRIPT = """[Section: Opening]
Microsoft's email went down for 3 days. [Source: a1]
[Section: The IPO]
The listing raised $1,500 million, Reuters reports. [Source: b2]
"""


def test_figures_must_come_from_the_script():
    assert nl.unsupported_numbers("Down for 3 days; $1500 million raised.", SCRIPT) == []
    assert nl.unsupported_numbers("Down for 4 days, 2026.", SCRIPT, "https://youtu.be/x") == ["2026", "4"]


def test_sources_are_the_ones_the_script_cites():
    items = [{"id": "a1", "title": "Outage", "source": "Reuters", "url": "https://r/1"},
             {"id": "zz", "title": "Other", "source": "X", "url": "https://x/2"},
             {"id": "b2", "title": "IPO", "source": "FT", "url": "https://f/3"}]
    block = nl.sources_block(items, SCRIPT)
    assert "https://r/1" in block and "https://f/3" in block and "https://x/2" not in block


class Client:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), 0

    @property
    def messages(self):
        outer = self

        class M:
            def create(self, **kw):
                outer.calls += 1
                return SimpleNamespace(content=[SimpleNamespace(type="text", text=outer.answers.pop(0))])
        return M()


def test_write_retries_once_on_an_invented_figure_and_saves_the_issue(tmp_path):
    (tmp_path / "script.md").write_text(SCRIPT, encoding="utf-8")
    (tmp_path / "items.json").write_text(json.dumps([{"id": "a1", "title": "Outage", "source": "R", "url": "https://r/1"}]))
    c = Client(["# Week\nDown for 9 days.", "# Week\nDown for 3 days.\n\nWatch the full episode: https://youtu.be/x"])
    issue, bad = nl.write(tmp_path, {"scripting": {"model": "m"}}, "https://youtu.be/x", c)
    assert c.calls == 2 and bad == [] and "## Sources" in issue
    assert (tmp_path / "newsletter.md").read_text(encoding="utf-8") == issue
    assert "Check before publishing" in nl.review_comment(issue, ["9"])
