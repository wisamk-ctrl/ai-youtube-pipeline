"""Phase C: promote/ignore decisions and the coverage report."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.ingestion.watchlist import load_watchlist  # noqa: E402
from pipeline.models import NewsItem  # noqa: E402
from pipeline.radar import coverage  # noqa: E402
from scripts.radar_decide import ignore, promote  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def test_promote_inserts_under_the_right_group_and_keeps_comments(tmp_path):
    wl = tmp_path / "watchlist.yaml"
    shutil.copy(ROOT / "config" / "watchlist.yaml", wl)
    state = tmp_path / "radar_state.json"
    msg = promote("Reflection AI", "models", "us", ar="ريفلكشن", aliases=["Beam"], hf="reflectionai",
                  watchlist=wl, state_path=state)
    assert msg.startswith("promoted")
    text = wl.read_text(encoding="utf-8")
    assert text.startswith("# ───")                                   # header comment intact
    us_block = text.split("      us:")[1].split("      eu:")[0]
    assert '- {name: Reflection AI, ar: ريفلكشن, aliases: [Beam], hf: reflectionai}' in us_block
    w = load_watchlist(wl)                                           # still valid YAML, still matches
    e = next(x for x in w.entities if x.name == "Reflection AI")
    assert e.track == "models" and e.group == "us" and "Beam" in e.aliases
    assert json.loads(state.read_text())["reflection"]["status"] == "promoted"
    assert promote("Mistral", "models", "eu", watchlist=wl, state_path=state).endswith("already on the watchlist")


def test_promote_rejects_unknown_group(tmp_path):
    wl = tmp_path / "watchlist.yaml"
    shutil.copy(ROOT / "config" / "watchlist.yaml", wl)
    try:
        promote("X Corp", "agents", "gulf", watchlist=wl, state_path=tmp_path / "s.json")
    except SystemExit as exc:
        assert "group 'gulf' not found" in str(exc)
    else:
        raise AssertionError("expected SystemExit")


def test_ignore_marks_state(tmp_path):
    state = tmp_path / "radar_state.json"
    assert ignore("Some Startup", state_path=state) == "ignored Some Startup"
    assert json.loads(state.read_text())["somestartup"]["status"] == "ignored"


def test_coverage_report_tracks_quiet_names(tmp_path):
    w = load_watchlist()
    path = tmp_path / "coverage.json"
    now = datetime.now(timezone.utc)
    mk = lambda ents: NewsItem(source="s", source_type="rss", title="t", summary="", url="u", published=now, entities=ents, track="models", region="us")  # noqa: E731
    for week in ("2026-W38", "2026-W39", "2026-W40"):
        coverage.record([mk(["OpenAI"]), mk(["Anthropic"])], w, week, path)
    data = coverage.record([mk(["OpenAI"]), mk(["G42"])], w, "2026-W41", path)
    md = coverage.report_md(data, w, "2026-W41")
    assert "models 2" in md and "us 2" in md
    quiet = md.split("**No news in 4 weeks**")[1].split(": ", 1)[1].split(", ")
    assert "Mistral" in quiet and "OpenAI" not in quiet and "Anthropic" not in quiet and "OpenAI Codex" in quiet
