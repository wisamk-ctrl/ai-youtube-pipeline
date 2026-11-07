"""Final audio pass, stock relevance, caption isolates (review 2026-11-07, Tier 1 #9/#10, Tier 2 subtitles)."""

import shutil
import subprocess
import wave

import pytest

from pipeline.post import audio, visual_assets
from pipeline.post.subtitles import isolate_latin

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def _tone(dest, seconds=12, amp=0.05):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    f"aevalsrc='{amp}*sin(2*PI*220*t)*gt(mod(t,3),0.5)':s=48000:d={seconds}", str(dest)], check=True)
    return dest


@ffmpeg
def test_two_pass_loudnorm_reaches_target(tmp_path):
    src = _tone(tmp_path / "quiet.wav")
    before = audio.measure(src)["input_i"]
    assert before < -20
    out = audio.normalise(src, tmp_path / "loud.wav", -14, -1.5, 7)
    m = audio.measure(out)
    assert abs(m["input_i"] + 14) < 1.0 and m["input_tp"] <= -1.0


def test_music_loop_is_deterministic_and_32_seconds(tmp_path):
    a = audio.music_loop(tmp_path / "a.wav")
    b = audio.music_loop(tmp_path / "b.wav")
    with wave.open(str(a)) as w:
        assert w.getframerate() == 48000 and w.getnchannels() == 2
        assert w.getnframes() == audio.LOOP_SECONDS * 48000
    assert a.read_bytes() == b.read_bytes()


@ffmpeg
def test_master_mixes_bed_and_hits_target_length(tmp_path):
    voice = _tone(tmp_path / "voice.wav", seconds=10)
    cfg = {"post": {"audio": {"music": "generated", "music_db": -24, "loudness_lufs": -14}}}
    out = audio.master(voice, tmp_path / "mix.wav", cfg, tmp_path / "work", cuts=[4.0])
    assert abs(audio.duration_of(out) - 10) < 0.1
    assert abs(audio.measure(out)["input_i"] + 14) < 1.0


def test_shift_srt_moves_captions_after_the_cut(tmp_path):
    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:01,000 --> 00:00:03,000\nا\n\n2\n00:00:04,000 --> 00:00:06,000\nب\n", encoding="utf-8")
    text = audio.shift_srt(srt, 3.5, 5.0, tmp_path / "o.srt").read_text(encoding="utf-8")
    assert "00:00:01,000 --> 00:00:03,000" in text and "00:00:09,000 --> 00:00:11,000" in text


def test_stock_tag_filter_rejects_off_topic_and_ranks_relevance(tmp_path):
    hits = [
        {"id": "pixabay_1", "animation": True, "duration": 20, "tags": "mermaid, fantasy, ocean", "width": 1920,
         "video_files": [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "x1"}]},
        {"id": "pixabay_2", "animation": True, "duration": 20, "tags": "sphere, abstract, glow", "width": 1920,
         "video_files": [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "x2"}]},
        {"id": "pixabay_3", "animation": False, "duration": 20, "tags": "network, neural, data, technology", "width": 1920,
         "video_files": [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "x3"}]},
        {"id": "pixabay_4", "animation": True, "duration": 20, "tags": "neural, network, woman, face", "width": 1920,
         "video_files": [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "x4"}]},
    ]
    assert visual_assets.relevance("neural network animation", "mermaid, network") is None
    assert visual_assets.relevance("woman using a laptop", "woman, laptop") == 2     # asked for: allowed
    for h in hits:
        (tmp_path / f"{h['id']}.mp4").write_bytes(b"")          # cached: no download
    used: set[str] = set()
    path, credit = visual_assets.fetch_stock("neural network animation", tmp_path, used, lambda q: hits, 1920, 5)
    assert credit["id"] == "pixabay_3"      # live footage that matches beats an unrelated or off-topic animation
    assert visual_assets.fetch_stock("neural network animation", tmp_path, used, lambda q: hits, 1920, 5) is None


def test_latin_runs_are_isolated():
    assert isolate_latin("نموذج GPT-5.1 من OpenAI") == "نموذج ⁨GPT-5.1⁩ من ⁨OpenAI⁩"
