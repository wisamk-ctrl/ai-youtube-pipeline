"""heard.json: a post re-run on the same talking_head skips Whisper (review Tier 2, CI)."""
import sys
import types

import pytest

from pipeline.post import subtitles
from pipeline.post.subtitles import HEARD_CACHE, Word, transcribe_words


@pytest.fixture
def fake_whisper(monkeypatch):
    calls = []

    class _W:
        def __init__(self, s, e, w):
            self.start, self.end, self.word = s, e, w

    class WhisperModel:
        def __init__(self, size, **_):
            self.size = size

        def transcribe(self, path, **_):
            calls.append((path, self.size))
            seg = types.SimpleNamespace(words=[_W(0.0, 0.4, " مرحبا"), _W(0.5, 0.9, " يا")])
            return iter([seg]), types.SimpleNamespace(language="ar", language_probability=0.99)

    monkeypatch.setitem(sys.modules, "faster_whisper", types.SimpleNamespace(WhisperModel=WhisperModel))
    return calls


def test_same_video_same_model_is_read_from_the_cache(tmp_path, fake_whisper):
    video = tmp_path / "talking_head.mp4"
    video.write_bytes(b"video-1")
    first = transcribe_words(video, "medium")
    assert (tmp_path / HEARD_CACHE).exists() and len(fake_whisper) == 1
    again = transcribe_words(video, "medium")     # repair, then run_post: one Whisper pass
    assert again == first and len(fake_whisper) == 1
    assert again[0] == Word(0.0, 0.4, " مرحبا")


def test_new_video_or_model_misses(tmp_path, fake_whisper):
    video = tmp_path / "talking_head.mp4"
    video.write_bytes(b"video-1")
    transcribe_words(video, "medium")
    transcribe_words(video, "small")              # other model
    video.write_bytes(b"video-2")                 # re-imported render, same name
    transcribe_words(video, "medium")
    assert len(fake_whisper) == 3
    transcribe_words(video, "medium")
    assert len(fake_whisper) == 3


def test_damaged_cache_and_opt_out(tmp_path, fake_whisper):
    video = tmp_path / "talking_head.mp4"
    video.write_bytes(b"video-1")
    (tmp_path / HEARD_CACHE).write_text("{not json", encoding="utf-8")
    assert transcribe_words(video, "medium")      # transcribes again, rewrites the cache
    assert len(fake_whisper) == 1
    transcribe_words(video, "medium", cache=False)
    assert len(fake_whisper) == 2


def test_run_post_and_repair_both_go_through_the_cached_function():
    import inspect

    import run_pipeline
    assert "transcribe_words(video)" in inspect.getsource(run_pipeline._repair_speech)
    assert "transcribe_words(video)" in inspect.getsource(subtitles.run_post)
