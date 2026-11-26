"""ElevenLabs narration for the voice-first route (pipeline/video/eleven_tts.py, founder 2026-11-26)."""
import base64

import yaml

from pipeline.video import eleven_tts as el
from pipeline.video.tts import is_current

AL = {"characters": list("Hi there <break time=\"1.0s\" /> now"),
      "character_start_times_seconds": [i * 0.1 for i in range(40)],
      "character_end_times_seconds": [i * 0.1 + 0.08 for i in range(40)]}


def test_words_from_character_timings_drop_break_tags():
    words = el.words_from_alignment(AL)
    assert [w["word"] for w in words] == ["Hi", "there", "now"]
    assert words[0]["start"] == 0.0 and words[1]["start"] == 0.3


def test_breaks_capped_at_three_seconds():
    assert el.ssml_breaks('a <break time="4.5s"/> b') == 'a <break time="3.0s" /> b'


class Resp:
    def __init__(self, code, data=None):
        self.status_code, self._d, self.text, self.headers = code, data, str(data), {}

    def json(self):
        return self._d


def test_speak_retries_a_rate_limit_then_returns_audio_and_words():
    calls = []

    class HTTP:
        def post(self, url, **kw):
            calls.append(kw["json"])
            return Resp(429) if len(calls) == 1 else Resp(200, {"audio_base64": base64.b64encode(b"mp3").decode(),
                                                               "alignment": AL})
    mp3, secs, words = el.speak("Hi there", "v", "k", {"model_id": "m", "stability": 0.5}, HTTP(), lambda s: None)
    assert mp3 == b"mp3" and round(secs, 2) == 3.98 and words[0]["word"] == "Hi"
    assert calls[0]["model_id"] == "m" and calls[0]["voice_settings"] == {"stability": 0.5}


def test_voice_week_writes_a_voice_file_the_assembler_accepts(tmp_path):
    chunks = [{"id": "01-face", "role": "face", "text": "Hello."}, {"id": "02-voice", "role": "voice", "text": "More."}]
    cfg = {"video": {"elevenlabs": {"voice_id": "v"}}}
    dest = el.voice_week(chunks, cfg, tmp_path / "voice.yaml", "2026-X1", key="k",
                         speak_fn=lambda t, v, k, s: (b"x", 1.5, [{"word": t, "start": 0, "end": 1}]),
                         publish_fn=lambda files, tag: {f.name: f"https://gh/{tag}/{f.name}" for f in files})
    data = yaml.safe_load(dest.read_text(encoding="utf-8"))
    assert data["01-face"]["audio"].startswith("https://gh/voice-2026-X1/2026-X1-01-face-")
    assert data["02-voice"]["duration"] == 1.5 and data["02-voice"]["words"][0]["word"] == "More."
    assert is_current(dest, chunks)
    from pipeline.video.voicefirst import load_voice
    entries = load_voice(dest, chunks)
    assert entries[0]["role"] == "voice" and entries[1]["words"][0][2] == "More."   # no face video yet: narration
