import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.youtube_partnerships import with_line  # noqa: E402


def test_line_goes_before_hashtags_once():
    d = "Intro\n\nSources:\n- a\n\n#AI #AINews"
    new = with_line(d, "partners@example.com")
    assert new.endswith("Partnerships: partners@example.com\n\n#AI #AINews")
    assert with_line(new, "partners@example.com") is None


def test_no_hashtags_and_limit():
    assert with_line("Short text", "p@x.com") == "Short text\n\nPartnerships: p@x.com"
    assert with_line("x" * 4990, "p@x.com") is None
