import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.short_check import caption_faults  # noqa: E402

SRT = """1
00:00:01,000 --> 00:00:03,000
in July and hacked into the AI platform Hugging

2
00:00:03,000 --> 00:00:03,800
Face

3
00:00:04,000 --> 00:00:05,000
Why?

4
00:00:05,000 --> 00:00:14,000
a caption that stays far too long
"""


def test_caption_faults():
    bad = caption_faults(SRT)
    assert any("alone" in b and "Face" in b for b in bad)
    assert not any("Why?" in b for b in bad)
    assert any("held 9.0 s" in b for b in bad)
