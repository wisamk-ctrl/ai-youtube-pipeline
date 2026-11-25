from pathlib import Path

import yaml

from pipeline.video import tts


class R:
    def __init__(self, code, data=None, headers=None, text=""):
        self.status_code, self._d, self.headers, self.text = code, data, headers or {}, text

    def json(self):
        return self._d


class Http:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    def post(self, url, **kw):
        self.calls.append((url, kw))
        return self.answers.pop(0)


def test_speak_retries_a_rate_limit_and_returns_the_audio():
    http = Http([R(429, headers={"Retry-After": "1"}), R(200, {"data": {"audio_url": "https://a/1.wav", "duration": 3.2}})])
    waits = []
    url, secs = tts.speak("Hello.", "v1", "en", "k", http=http, sleep=waits.append)
    assert (url, secs) == ("https://a/1.wav", 3.2) and waits == [1.0]
    u, kw = http.calls[0]
    assert u == tts.URL and kw["headers"]["X-Api-Key"] == "k"
    assert kw["json"] == {"voice_id": "v1", "text": "Hello.", "language": "en", "model": "heygen-voice-1"}


def test_speak_raises_on_a_client_error():
    try:
        tts.speak("x", "v", "en", "k", http=Http([R(400, text="bad voice")]), sleep=lambda s: None)
    except RuntimeError as e:
        assert "400" in str(e)
    else:
        raise AssertionError("no error")


def test_speak_falls_back_to_ellipses_when_the_voice_cannot_take_break_tags():
    """2026-11-20: W47-en's render failed with HTTP 400 'break tags are not supported for instant voice clones' —
    the first whole episode voiced through the API (W46-en was voiced by hand through the connector)."""
    err = R(400, text='{"error":{"code":"invalid_parameter","message":"break tags are not supported for instant voice clones"}}')
    http = Http([err, R(200, {"data": {"audio_url": "https://a/2.wav", "duration": 5.0}})])
    url, _ = tts.speak('One. <break time="0.8s"/> Two.', "v", "en", "k", http=http, sleep=lambda s: None)
    assert url == "https://a/2.wav"
    assert "<break" not in http.calls[1][1]["json"]["text"] and "..." in http.calls[1][1]["json"]["text"]


def test_voice_week_writes_a_voice_list_the_assembler_reads(tmp_path):
    cfg = {"language": "en", "video": {"heygen": {"voice_id_en": "EN"}}}
    chunks = [{"id": "01-face", "role": "face", "text": "A."}, {"id": "02-voice", "role": "voice", "text": "B."}]
    seen = []

    def fake(text, voice, lang, key, model):
        seen.append((text, voice, lang))
        return f"https://a/{text}", 1.5

    dest = tts.voice_week(chunks, cfg, tmp_path / "voice.yaml", key="k", speak_fn=fake)
    assert seen == [("A.", "EN", "en"), ("B.", "EN", "en")]
    data = yaml.safe_load(dest.read_text())
    assert {k: {f: v[f] for f in ("audio", "duration")} for k, v in data.items()} == \
        {"01-face": {"audio": "https://a/A.", "duration": 1.5}, "02-voice": {"audio": "https://a/B.", "duration": 1.5}}
    from pipeline.video.voicefirst import load_voice
    entries = load_voice(dest, chunks)
    assert [e["role"] for e in entries] == ["voice", "voice"]       # a face chunk without video is narration


def test_a_changed_script_is_voiced_again(tmp_path):
    from pipeline.video.tts import is_current, voice_week
    cfg = {"language": "en", "video": {"heygen": {"voice_id_en": "EN"}}}
    chunks = [{"id": "01-voice", "role": "voice", "text": "Old line."}]
    dest = voice_week(chunks, cfg, tmp_path / "voice.yaml", key="k",
                      speak_fn=lambda *a, **k: ("https://x/a.wav", 1.0))
    assert is_current(dest, chunks)
    assert is_current(dest, [{"id": "01-voice", "role": "voice", "text": "Old   line."}])   # spacing only
    assert not is_current(dest, [{"id": "01-voice", "role": "voice", "text": "New line with a view."}])
    assert not is_current(dest, chunks + [{"id": "02-voice", "role": "voice", "text": "More."}])
    old = tmp_path / "old.yaml"
    old.write_text("01-voice: {audio: 'https://x/a.wav', duration: 1.0}\n")   # before the text stamp
    assert not is_current(old, chunks)


def test_a_speech_style_reaches_heygen_and_tags_the_text():
    """Founder 2026-11-25: the trailer's voice should sound much more excited. HeyGen instant clones take
    speed and pitch_variance in the body and perform an [excited] tag that spans about 233 characters."""
    http = Http([R(200, {"data": {"audio_url": "https://a/3.wav", "duration": 2.0}})])
    tts.speak("Hi.", "v", "en", "k", http=http, sleep=lambda s: None, opts={"speed": 1.06, "pitch_variance": 1.3})
    body = http.calls[0][1]["json"]
    assert body["speed"] == 1.06 and body["pitch_variance"] == 1.3 and body["text"] == "Hi."
    long = " ".join(["This sentence is about forty characters."] * 8)
    tagged = tts.styled(long, {"tag": "excited"})
    assert tagged.startswith("[excited] ") and tagged.count("[excited]") == 2
    assert tts.styled("Plain.", {}) == "Plain."


def test_voice_week_applies_the_style_and_a_new_style_voices_again(tmp_path):
    from pipeline.video.tts import is_current, voice_week
    cfg = {"language": "en", "video": {"heygen": {"voice_id_en": "EN"}}}
    chunks = [{"id": "01-voice", "role": "voice", "text": "Big news."}]
    seen = []

    def fake(text, voice, lang, key, model, opts=None):
        seen.append((text, opts))
        return "https://x/a.wav", 1.0

    style = {"tag": "excited", "speed": 1.06}
    dest = voice_week(chunks, cfg, tmp_path / "voice.yaml", key="k", speak_fn=fake, style=style)
    assert seen == [("[excited] Big news.", {"speed": 1.06})]
    assert is_current(dest, chunks, style) and not is_current(dest, chunks)
