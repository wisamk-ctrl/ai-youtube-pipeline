"""Render speed (2026-11-21): per-stage timing, fewer full re-encodes, parallel stock fetches, parallel
Shorts, and the preview made in the render job. Output quality must not drop: same length, 4K master,
-14 LUFS."""
import json
import time
from pathlib import Path

import pytest

from pipeline import timing


def test_stage_records_seconds_and_writes_summary(tmp_path):
    t = timing.Timer()
    with t.stage("edited cut"):
        time.sleep(0.01)
    with t.stage("edited cut"):          # a stage met twice adds up
        time.sleep(0.01)
    with t.stage("overlays"):
        pass
    assert list(t.seconds) == ["edited cut", "overlays"]
    assert t.seconds["edited cut"] >= 0.02
    path = t.write(tmp_path / "timings.json")
    data = json.loads(path.read_text())
    assert [s["stage"] for s in data["stages"]] == ["edited cut", "overlays"]
    assert data["total_s"] >= 0.02


def test_stage_records_time_even_when_the_stage_fails():
    t = timing.Timer()
    with pytest.raises(RuntimeError):
        with t.stage("master"):
            raise RuntimeError("boom")
    assert "master" in t.seconds


def test_table_is_markdown():
    t = timing.Timer()
    t.seconds.update({"a": 61.0, "b": 5.0})
    table = t.table()
    assert "| a | 61 s (1:01) |" in table and table.splitlines()[0].startswith("| Stage")


# ── One final pass: the 1080p cut and the 4K master from one decode ────────────────────────────────
import shutil
import subprocess

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def _has_libass() -> bool:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
    return " subtitles " in r.stdout


@pytest.fixture
def captions_or_null(monkeypatch):
    """Real libass captions where ffmpeg has them (the runner); a `null` filter elsewhere, so the rest of the
    graph (split, both encoders, the end card) is still exercised by a real ffmpeg."""
    from pipeline.post import subtitles
    if not _has_libass():
        monkeypatch.setattr(subtitles, "_subs_filter", lambda *a: "null")


def _probe(path: Path) -> tuple[int, float]:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height:format=duration",
                        "-of", "json", str(path)], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    return int(d["streams"][0]["height"]), float(d["format"]["duration"])


def _clip(dest: Path, seconds: float, size: str = "320x180", tone: int = 440) -> Path:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"testsrc=size={size}:rate=30",
                    "-f", "lavfi", "-i", f"sine=frequency={tone}:sample_rate=48000", "-t", str(seconds),
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", str(dest)], check=True)
    return dest


@ffmpeg
@pytest.mark.parametrize("with_tail", [False, True])
def test_burn_in_writes_the_upload_master_in_the_same_pass(tmp_path, with_tail, captions_or_null):
    from pipeline.post import subtitles
    src = _clip(tmp_path / "cut.mp4", 2.0)
    tail = _clip(tmp_path / "tail.mp4", 1.0, tone=660) if with_tail else None
    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,500\nHello there\n", encoding="utf-8")
    calls = []
    real = subtitles._ffmpeg
    subtitles._ffmpeg = lambda *a: (calls.append(a), real(*a))[1]
    try:
        final = subtitles.burn_in(src, srt, tmp_path / "final.mp4", tail=tail, master=(tmp_path / "big.mp4", 360, "ultrafast"),
                                  preset="ultrafast")
    finally:
        subtitles._ffmpeg = real
    assert len(calls) == 1                              # one decode, one filter graph, two encodes
    h, d = _probe(final)
    bh, bd = _probe(tmp_path / "big.mp4")
    assert h == 180 and bh == 360
    assert abs(d - bd) < 0.1 and abs(d - (3.0 if with_tail else 2.0)) < 0.15


# ── Parallel ffmpeg jobs ─────────────────────────────────────────────────────────────────────────────
def test_run_all_keeps_order_and_runs_at_once():
    import threading
    from pipeline.post import jobs
    seen, lock, peak = [], threading.Lock(), [0]
    live = [0]

    def job(k):
        def run():
            with lock:
                live[0] += 1
                peak[0] = max(peak[0], live[0])
            time.sleep(0.05)
            with lock:
                live[0] -= 1
            seen.append(k)
            return k * 10
        return run
    assert jobs.run_all([job(k) for k in range(6)], workers=3) == [0, 10, 20, 30, 40, 50]
    assert peak[0] == 3


def test_run_all_raises_the_first_failure():
    from pipeline.post import jobs

    def bad():
        raise ValueError("segment 3")
    with pytest.raises(ValueError, match="segment 3"):
        jobs.run_all([lambda: 1, bad, lambda: 2], workers=2)


def test_workers_from_settings(monkeypatch):
    from pipeline.post import jobs
    assert jobs.workers({"post": {"workers": 3}}) == 3
    monkeypatch.setattr(jobs.os, "cpu_count", lambda: 8)
    assert jobs.workers({"post": {"workers": 0}}) == 8
    assert jobs.workers({}) == 4


def test_intermediate_encode_settings():
    from pipeline.post.overlays import intermediate
    assert intermediate({"post": {"intermediate": {"preset": "superfast", "crf": 14}}}) == ("superfast", 14)
    assert intermediate({}) == ("veryfast", 16)


def test_detail_stages_are_shown_but_not_added_to_the_total():
    t = timing.Timer()
    t.seconds["visuals"] = 100.0
    t.add_detail("visuals: card frames", 60.0)
    t.add_detail("visuals: card frames", 5.0)
    assert t.total() == 100.0 and t.details["visuals: card frames"] == 65.0
    assert "| ↳ visuals: card frames | 65 s (1:05) |" in t.table()


# ── Stock: smallest file that fills the frame, fetched side by side, kept across runs ─────────────────
from pipeline.post import visual_assets


def _vid(i, tags="neural network", files=None):
    return {"id": f"pixabay_{i}", "duration": 20, "animation": True, "tags": tags, "width": 1920,
            "video_files": files or [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": f"https://cdn/{i}.mp4"}]}


def test_pick_file_takes_the_smaller_file_at_the_same_width():
    v = _vid(1, files=[{"file_type": "video/mp4", "width": 1920, "height": 1080, "size": 90_000_000, "link": "big"},
                       {"file_type": "video/mp4", "width": 1920, "height": 1080, "size": 9_000_000, "link": "small"},
                       {"file_type": "video/mp4", "width": 3840, "height": 2160, "size": 300_000_000, "link": "4k"}])
    assert visual_assets.pick_file(v, 1920)["link"] == "small"


def test_prefetch_downloads_each_shots_likely_clip_side_by_side(tmp_path, monkeypatch):
    import threading
    hits = {"neural network": [_vid(1), _vid(2), _vid(3)], "data centre": [_vid(4, "data centre"), _vid(5, "data centre")]}
    got, lock, live, peak = [], threading.Lock(), [0], [0]

    def fake_download(url, dest):
        with lock:
            live[0] += 1
            peak[0] = max(peak[0], live[0])
        time.sleep(0.05)
        dest.write_bytes(b"x")
        with lock:
            live[0] -= 1
            got.append(url)
        return dest
    monkeypatch.setattr("pipeline.video.common.download", fake_download)
    shots = [("neural network", 5.0), ("neural network", 5.0), ("data centre", 5.0)]
    n = visual_assets.prefetch_stock(shots, tmp_path, {"pixabay_3"}, lambda q: hits[q], 1920, workers=8, spare=0)
    # the second shot with the same search takes the next unused clip, as fetch_stock will; the blocklist is honoured
    assert sorted(got) == ["https://cdn/1.mp4", "https://cdn/2.mp4", "https://cdn/4.mp4"] and n == 3
    assert peak[0] >= 2
    # cached on disk: a second prefetch downloads nothing
    got.clear()
    assert visual_assets.prefetch_stock(shots, tmp_path, {"pixabay_3"}, lambda q: hits[q], 1920, workers=8, spare=0) == 0


def test_prefetch_survives_a_failed_search_or_download(tmp_path, monkeypatch):
    def boom(url, dest):
        raise OSError("reset")
    monkeypatch.setattr("pipeline.video.common.download", boom)

    def search(q):
        if q == "bad":
            raise RuntimeError("429")
        return [_vid(7)]
    assert visual_assets.prefetch_stock([("bad", 5.0), ("neural network", 5.0)], tmp_path, set(), search, 1920) == 0


def test_stock_cache_lives_outside_the_week(monkeypatch, tmp_path):
    monkeypatch.setenv("MEDIA_CACHE", str(tmp_path / "mc"))
    assert visual_assets.media_cache("stock") == tmp_path / "mc" / "stock"
    assert (tmp_path / "mc" / "stock").is_dir()


def test_prune_cache_keeps_the_newest_files_under_the_limit(tmp_path):
    import os
    for k in range(5):
        f = tmp_path / f"{k}.mp4"
        f.write_bytes(b"x" * 1000)
        os.utime(f, (1000 + k, 1000 + k))
    removed = visual_assets.prune_cache(tmp_path, max_bytes=2500)
    assert removed == 3 and sorted(p.name for p in tmp_path.iterdir()) == ["3.mp4", "4.mp4"]


# ── Captions without a second Whisper pass: HeyGen's word timings, else a faster model for alignment ───
def test_voice_yaml_words_are_read(tmp_path):
    from pipeline.video import voicefirst
    chunks = [{"id": "01-face", "role": "face", "text": "a"}, {"id": "02-voice", "role": "voice", "text": "b c"}]
    p = tmp_path / "voice.yaml"
    p.write_text("01-face: {audio: https://r/a.wav, video: https://f/a.mp4, words: [{word: Hello, start: 0.1, end: 0.5}]}\n"
                 "02-voice: {audio: https://r/b.wav, words: [[0.0, 0.3, Good], [0.35, 0.9, evening]]}\n")
    got = voicefirst.load_voice(p, chunks)
    assert got[0]["words"] == [(0.1, 0.5, "Hello")]
    assert got[1]["words"] == [(0.0, 0.3, "Good"), (0.35, 0.9, "evening")]
    p.write_text("01-face: {audio: https://r/a.wav, words: [nonsense]}\n02-voice: https://r/b.wav\n")
    with pytest.raises(ValueError, match="words"):
        voicefirst.load_voice(p, chunks)


def test_chunk_words_move_onto_the_narration_timeline():
    from pipeline.video import voicefirst
    w = voicefirst.chunk_words({"words": [(0.2, 0.6, "Hi"), (0.7, 1.0, "all")]}, offset=10.0, tempo=0.5)
    assert [(x.start, x.end, x.word) for x in w] == [(10.4, 11.2, "Hi"), (11.4, 12.0, "all")]
    assert voicefirst.chunk_words({}, 0.0, 1.0) is None


def test_whisper_model_per_language(monkeypatch):
    from pipeline.post import subtitles
    monkeypatch.delenv("WHISPER_MODEL", raising=False)
    monkeypatch.delenv("WHISPER_MODEL_EN", raising=False)
    assert subtitles.whisper_model("en") == "large-v3"
    monkeypatch.setenv("WHISPER_MODEL", "medium")
    assert subtitles.whisper_model("en") == "medium" and subtitles.whisper_model("ar") == "medium"
    monkeypatch.setenv("WHISPER_MODEL_EN", "small.en")    # English captions only align known text to the voice
    assert subtitles.whisper_model("en") == "small.en" and subtitles.whisper_model("ar") == "medium"


# ── Cue cards: each card image decoded once, not 2× a second for the whole episode ────────────────────
@ffmpeg
def test_overlay_draws_each_card_only_in_its_window_and_reads_each_image_once(tmp_path):
    import numpy as np
    from pipeline.post import overlays
    from pipeline.script_format import Cue
    src = _clip(tmp_path / "cut.mp4", 4.0, size="480x270")
    pngs = []
    for k, colour in enumerate(("red", "blue")):
        png = tmp_path / f"c{k}.png"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"color=c={colour}:s=480x270",
                        "-frames:v", "1", str(png)], check=True)
        pngs.append(png)
    cue = Cue(kind="onscreen", text="x", at_word=0, at_seconds=0.0)
    cards = [overlays.Card(cue, 0.5, 1.0, pngs[0]), overlays.Card(cue, 2.5, 1.0, pngs[1])]
    graph = overlays.card_graph(cards)
    assert "-loop" not in " ".join(graph[0]) and graph[1].count("loop=loop=-1:size=1") == 2
    out = overlays.overlay(src, cards, tmp_path / "with.mp4", enc=("ultrafast", 16))

    def px(t):
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(out), "-frames:v", "1", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
        return np.frombuffer(r.stdout, dtype=np.uint8).reshape(270, 480, 3)[135, 240].astype(int)
    red, blue, none = px(1.0), px(3.0), px(2.0)
    assert red[0] > 200 and red[2] < 60
    assert blue[2] > 200 and blue[0] < 60
    assert not (none[0] > 200 and none[1] < 60 and none[2] < 60)
    assert overlays._frames(out) == overlays._frames(src)
