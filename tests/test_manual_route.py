"""Manual HeyGen route: paste pack and video import."""

import shutil
import subprocess
from pathlib import Path

import pytest

from pipeline.config import load_settings
from pipeline.video import manual

SCRIPT = """[Section: الافتتاحية]

[Show B-Roll: skyline]

خبر أول عن الموديلات.

[Pause]

[On-Screen Text: 40 مليار]

وخبر تاني عن الشرائح.
"""


def test_paste_pack_strips_markers_and_keeps_pauses():
    pack = manual.paste_pack(SCRIPT, load_settings(), "2026-W43-jo")
    assert "## Scene 1" in pack
    assert "[Section" not in pack and "[Show B-Roll" not in pack and "On-Screen" not in pack
    assert "<break" not in pack and "..." in pack
    assert "خبر أول" in pack and "وخبر تاني" in pack


def test_paste_scenes_fit_the_chunk_limit():
    cfg = load_settings()
    long = "\n\n".join(["جملة طويلة شوي عن الذكاء الاصطناعي بالمنطقة." for _ in range(200)])
    scenes = manual.paste_scenes(long, cfg)
    assert len(scenes) > 1
    assert all(len(s) <= cfg["video"]["max_chars_per_chunk"] for s in scenes)


@pytest.mark.parametrize("ref,expected", [
    ("https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz012345/view?usp=sharing",
     "https://drive.usercontent.google.com/download?id=1AbCdEfGhIjKlMnOpQrStUvWxYz012345&export=download&confirm=t"),
    ("https://www.dropbox.com/scl/fi/abc/ep.mp4?rlkey=x&dl=0", "https://www.dropbox.com/scl/fi/abc/ep.mp4?rlkey=x&dl=1"),
    ("https://example.com/ep.mp4", "https://example.com/ep.mp4"),
])
def test_resolve_share_links(ref, expected):
    assert manual.resolve(ref) == expected


def test_resolve_heygen_id_and_share_link(monkeypatch):
    seen = []
    monkeypatch.setattr(manual, "heygen_url", lambda vid, key: seen.append(vid) or f"https://cdn/{vid}.mp4")
    vid = "0123456789abcdef0123456789abcdef"
    assert manual.resolve(vid) == f"https://cdn/{vid}.mp4"
    assert manual.resolve(f"https://app.heygen.com/share/{vid}") == f"https://cdn/{vid}.mp4"
    assert seen == [vid, vid]


def test_resolve_rejects_garbage():
    with pytest.raises(ValueError):
        manual.resolve("not a link")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_probe_accepts_a_talking_head_and_rejects_silence(tmp_path: Path):
    good = tmp_path / "good.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=320x180:d=12",
                    "-f", "lavfi", "-i", "sine=d=12", "-shortest", str(good)], check=True)
    assert manual.probe(good)["duration"] >= 10
    mute = tmp_path / "mute.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=320x180:d=12", str(mute)], check=True)
    with pytest.raises(ValueError):
        manual.probe(mute)
